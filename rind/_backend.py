"""
Core implementation of the rind PEP 517 build backend.
"""

import hashlib
import io
import json
import sys
import zipfile
from base64 import urlsafe_b64encode
from pathlib import Path

from packaging.utils import canonicalize_name

# tomllib is built-in from Python 3.11+, use tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# This file is included in the sdist to cache inherited metadata,
# allowing wheels to be built from sdists without the parent pyproject.toml
_CACHED_METADATA_FILE = ".rind_inherited.json"


def _get_rind_version():
    """Get rind's own version for the wheel generator tag."""
    try:
        from ._version import version

        return version
    except ImportError:
        return "0.0.0"


def _get_version(root=".."):
    """Get version from git using setuptools_scm."""
    from setuptools_scm import get_version

    # Resolve relative to cwd (where pyproject.toml is), not this file
    root_path = Path.cwd() / root
    return get_version(root=str(root_path.resolve()))


def _safe_name(name):
    """Return wheel-safe name (lowercase, underscores).

    Uses PEP 503 normalization, then replaces hyphens with underscores
    for wheel/sdist filenames per PEP 427.
    """
    return canonicalize_name(name).replace("-", "_")


def _wheel_name(name, version):
    """Generate wheel filename per PEP 427."""
    return f"{_safe_name(name)}-{version}-py3-none-any.whl"


def _parse_pyproject(path="pyproject.toml"):
    """Parse pyproject.toml and return data."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def _record_hash(data):
    """Calculate hash for RECORD file.

    RECORD uses base64url-encoded sha256 without padding.
    """
    digest = hashlib.sha256(data).digest()
    hash_str = urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"sha256={hash_str}"


def _get_inherited_metadata(tool_config):
    """Get inherited metadata from parent pyproject.toml or cached file.

    The cache file is used when building a wheel from an sdist, where
    the parent pyproject.toml is not available.
    """
    # First check for cached metadata (present when building from sdist)
    cache_path = Path(_CACHED_METADATA_FILE)
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    # Otherwise try to load from the parent pyproject.toml
    inherit_path = tool_config.get("inherit-metadata")
    if inherit_path:
        resolved_path = (Path.cwd() / inherit_path).resolve()
        if resolved_path.exists():
            inherited_pyproject = _parse_pyproject(resolved_path)
            return inherited_pyproject.get("project", {})

    return {}


def _save_inherited_metadata(inherited, dest_dir="."):
    """Save inherited metadata to cache file for inclusion in sdist."""
    cache_path = Path(dest_dir) / _CACHED_METADATA_FILE
    with open(cache_path, "w") as f:
        json.dump(inherited, f, indent=2)
    return cache_path


def _build_metadata(config_settings=None):
    """Build and return all metadata needed for the package."""
    pyproject = _parse_pyproject()
    tool_config = pyproject.get("tool", {}).get("rind", {})

    # Get inherited metadata from parent pyproject.toml (or cache)
    inherited = _get_inherited_metadata(tool_config)
    local_project = pyproject.get("project", {})

    # Name is required - check tool.rind first, then [project]
    name = tool_config.get("name") or local_project.get("name")
    if not name:
        raise ValueError(
            "Package name must be specified in [tool.rind] name = ... "
            "or [project] name = ..."
        )

    # Get version from git tags via setuptools_scm
    version = _get_version(root=tool_config.get("version-root", ".."))

    # Determine core package name:
    # 1. Explicit core-package in config
    # 2. Inherited package name (if using inherit-metadata)
    core_package = tool_config.get("core-package")
    if not core_package:
        if inherited.get("name"):
            core_package = inherited["name"]
        else:
            raise ValueError(
                "Core package name must be specified via [tool.rind] core-package = ... "
                "or by using inherit-metadata to inherit from a parent pyproject.toml"
            )

    # Build the main dependency on the core package
    include_extras = tool_config.get("include-extras", [])
    if include_extras:
        # Include specified extras: core-package[extra1,extra2]==version
        extras_str = ",".join(include_extras)
        core_dep = f"{core_package}[{extras_str}]=={version}"
    else:
        core_dep = f"{core_package}=={version}"

    # Collect all dependencies: core package + any additional
    dependencies = [core_dep]
    dependencies.extend(tool_config.get("additional-dependencies", []))

    # Build passthrough extras - these re-expose core package extras
    # with the same pinned version
    optional_deps = {}
    for extra_name in tool_config.get("passthrough-extras", []):
        optional_deps[extra_name] = [f"{core_package}[{extra_name}]=={version}"]

    # Helper to get field with priority: tool.rind > [project] > inherited
    def get_field(field):
        if field in tool_config:
            return tool_config[field]
        if field in local_project:
            return local_project[field]
        return inherited.get(field)

    # Collect all metadata fields that can be inherited or overridden
    metadata_fields = {
        "description": get_field("description"),
        "requires-python": get_field("requires-python"),
        "license": get_field("license"),
        "authors": get_field("authors"),
        "urls": get_field("urls"),
        "classifiers": get_field("classifiers"),
        "keywords": get_field("keywords"),
    }

    return {
        "name": name,
        "version": version,
        "metadata_fields": metadata_fields,
        "dependencies": dependencies,
        "optional_deps": optional_deps,
        "core_package": core_package,
        "inherited": inherited,
    }


# =============================================================================
# PEP 517 Build Backend Hooks
# =============================================================================
# These are the standard hooks called by build frontends (pip, build, etc.)


def get_requires_for_build_wheel(config_settings=None):
    """Return build dependencies for wheel."""
    return ["setuptools_scm"]


def get_requires_for_build_sdist(config_settings=None):
    """Return build dependencies for sdist."""
    return ["setuptools_scm"]


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """Build a wheel containing only metadata, no code.

    This is the main PEP 517 hook for building wheels. The resulting wheel
    contains only the ``.dist-info`` directory with package metadata.
    """
    meta = _build_metadata(config_settings)

    name = meta["name"]
    version = meta["version"]
    fields = meta["metadata_fields"]
    dependencies = meta["dependencies"]
    optional_deps = meta["optional_deps"]

    # Build METADATA file content (PEP 566 / Core Metadata)
    metadata_lines = [
        "Metadata-Version: 2.1",
        f"Name: {name}",
        f"Version: {version}",
    ]

    # Add optional metadata fields if present
    if fields.get("description"):
        metadata_lines.append(f"Summary: {fields['description']}")

    if fields.get("requires-python"):
        metadata_lines.append(f"Requires-Python: {fields['requires-python']}")

    if fields.get("license"):
        lic = fields["license"]
        # License can be a string or dict with 'text' key (pyproject.toml format)
        if isinstance(lic, dict):
            metadata_lines.append(f"License: {lic.get('text', '')}")
        else:
            metadata_lines.append(f"License: {lic}")

    if fields.get("urls"):
        for label, url in fields["urls"].items():
            metadata_lines.append(f"Project-URL: {label}, {url}")

    if fields.get("authors"):
        # Extract names and emails from author dicts
        authors = [a.get("name", "") for a in fields["authors"] if "name" in a]
        if authors:
            metadata_lines.append(f"Author: {', '.join(authors)}")
        emails = [a.get("email", "") for a in fields["authors"] if "email" in a]
        if emails:
            metadata_lines.append(f"Author-email: {', '.join(emails)}")

    if fields.get("classifiers"):
        for classifier in fields["classifiers"]:
            metadata_lines.append(f"Classifier: {classifier}")

    if fields.get("keywords"):
        keywords = fields["keywords"]
        if isinstance(keywords, list):
            keywords = ",".join(keywords)
        metadata_lines.append(f"Keywords: {keywords}")

    # Add required dependencies
    for dep in dependencies:
        metadata_lines.append(f"Requires-Dist: {dep}")

    # Add optional dependencies (extras)
    for extra_name, extra_deps in optional_deps.items():
        metadata_lines.append(f"Provides-Extra: {extra_name}")
        for dep in extra_deps:
            metadata_lines.append(f"Requires-Dist: {dep}; extra == '{extra_name}'")

    metadata_content = "\n".join(metadata_lines) + "\n"

    # Build WHEEL file content (PEP 427)
    wheel_content = f"""\
Wheel-Version: 1.0
Generator: rind {_get_rind_version()}
Root-Is-Purelib: true
Tag: py3-none-any
"""

    # Create the wheel zip file
    wheel_path = Path(wheel_directory) / _wheel_name(name, version)
    dist_info = f"{_safe_name(name)}-{version}.dist-info"

    # RECORD tracks all files in the wheel with their hashes
    record_entries = []

    with zipfile.ZipFile(wheel_path, "w", zipfile.ZIP_DEFLATED) as whl:
        # Write METADATA
        metadata_bytes = metadata_content.encode("utf-8")
        whl.writestr(f"{dist_info}/METADATA", metadata_bytes)
        record_entries.append(
            f"{dist_info}/METADATA,{_record_hash(metadata_bytes)},{len(metadata_bytes)}"
        )

        # Write WHEEL
        wheel_bytes = wheel_content.encode("utf-8")
        whl.writestr(f"{dist_info}/WHEEL", wheel_bytes)
        record_entries.append(
            f"{dist_info}/WHEEL,{_record_hash(wheel_bytes)},{len(wheel_bytes)}"
        )

        # Write RECORD (no hash for itself per spec)
        record_entries.append(f"{dist_info}/RECORD,,")
        record_content = "\n".join(record_entries) + "\n"
        whl.writestr(f"{dist_info}/RECORD", record_content.encode("utf-8"))

    return wheel_path.name


def build_sdist(sdist_directory, config_settings=None):
    """Build a minimal source distribution.

    The sdist contains the pyproject.toml and a cached copy of the inherited
    metadata (so that wheels can be built from the sdist without access to
    the parent pyproject.toml).
    """
    import tarfile

    meta = _build_metadata(config_settings)
    name = meta["name"]
    version = meta["version"]
    description = meta["metadata_fields"].get("description", "")
    inherited = meta["inherited"]

    # sdist filename uses underscores per PEP 625
    sdist_name = f"{_safe_name(name)}-{version}"
    sdist_path = Path(sdist_directory) / f"{sdist_name}.tar.gz"

    # Cache inherited metadata so wheel builds from sdist work
    cache_file = _save_inherited_metadata(inherited)

    try:
        with tarfile.open(sdist_path, "w:gz") as tar:
            # Include the pyproject.toml
            tar.add("pyproject.toml", f"{sdist_name}/pyproject.toml")

            # Include cached inherited metadata
            tar.add(str(cache_file), f"{sdist_name}/{_CACHED_METADATA_FILE}")

            # Include PKG-INFO (required by sdist spec)
            pkg_info = f"""\
Metadata-Version: 2.1
Name: {name}
Version: {version}
Summary: {description}
"""
            pkg_info_bytes = pkg_info.encode("utf-8")
            info = tarfile.TarInfo(f"{sdist_name}/PKG-INFO")
            info.size = len(pkg_info_bytes)
            tar.addfile(info, io.BytesIO(pkg_info_bytes))
    finally:
        # Clean up temporary cache file
        cache_file.unlink(missing_ok=True)

    return sdist_path.name
