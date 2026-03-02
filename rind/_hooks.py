"""
PEP 517 build backend hooks for rind.

These are the standard hooks called by build frontends (pip, build, etc.)
"""

import io
import zipfile
from pathlib import Path

from ._metadata import build_metadata
from ._utils import (
    get_core_pyproject_path,
    get_rind_version,
    parse_pyproject,
    record_hash,
    safe_name,
    wheel_name,
)


def _is_sdist_mode():
    """Check if we're building from an sdist (no core-path present)."""
    pyproject = parse_pyproject()
    tool_config = pyproject.get("tool", {}).get("rind", {})
    return not tool_config.get("core-path")


def get_requires_for_build_wheel(config_settings=None):
    """Return build dependencies for wheel.

    The dependencies depend on how the core package determines its version:
    - Sdist mode (no core-path): no extra deps needed, version is in [project]
    - Static version: no extra deps needed
    - setuptools_scm/hatch-vcs: needs setuptools_scm
    - Other backends: needs pyproject_hooks + core's build deps
    """
    # Check if we're building from an sdist
    if _is_sdist_mode():
        # Building from sdist - version is in [project], no deps needed
        return []

    # Building from source - determine what we need for version detection
    pyproject = parse_pyproject()
    tool_config = pyproject.get("tool", {}).get("rind", {})

    core_path = get_core_pyproject_path(tool_config)
    core_pyproject = parse_pyproject(core_path)

    from ._version_helpers import get_version_requires

    return get_version_requires(core_pyproject)


def get_requires_for_build_sdist(config_settings=None):
    """Return build dependencies for sdist.

    Same logic as wheel - we need to determine the version.
    """
    pyproject = parse_pyproject()
    tool_config = pyproject.get("tool", {}).get("rind", {})

    core_path = get_core_pyproject_path(tool_config)
    core_pyproject = parse_pyproject(core_path)

    from ._version_helpers import get_version_requires

    return get_version_requires(core_pyproject)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """Build a wheel containing only metadata, no code.

    This is the main PEP 517 hook for building wheels. The resulting wheel
    contains only the ``.dist-info`` directory with package metadata.
    """
    meta = build_metadata(config_settings)

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
Generator: rind {get_rind_version()}
Root-Is-Purelib: true
Tag: py3-none-any
"""

    # Create the wheel zip file
    wheel_path = Path(wheel_directory) / wheel_name(name, version)
    dist_info = f"{safe_name(name)}-{version}.dist-info"

    # RECORD tracks all files in the wheel with their hashes
    record_entries = []

    with zipfile.ZipFile(wheel_path, "w", zipfile.ZIP_DEFLATED) as whl:
        # Write METADATA
        metadata_bytes = metadata_content.encode("utf-8")
        whl.writestr(f"{dist_info}/METADATA", metadata_bytes)
        record_entries.append(
            f"{dist_info}/METADATA,{record_hash(metadata_bytes)},{len(metadata_bytes)}"
        )

        # Write WHEEL
        wheel_bytes = wheel_content.encode("utf-8")
        whl.writestr(f"{dist_info}/WHEEL", wheel_bytes)
        record_entries.append(
            f"{dist_info}/WHEEL,{record_hash(wheel_bytes)},{len(wheel_bytes)}"
        )

        # Write RECORD (no hash for itself per spec)
        record_entries.append(f"{dist_info}/RECORD,,")
        record_content = "\n".join(record_entries) + "\n"
        whl.writestr(f"{dist_info}/RECORD", record_content.encode("utf-8"))

    return wheel_path.name


def _generate_resolved_pyproject(meta, original_pyproject):
    """Generate a resolved pyproject.toml with all values hardcoded.

    This pyproject.toml can be used to build a wheel without access to
    the core package's pyproject.toml or git tags.
    """
    import tomli_w

    fields = meta["metadata_fields"]

    # Build the project section
    project = {
        "name": meta["name"],
        "version": meta["version"],
    }

    if fields.get("description"):
        project["description"] = fields["description"]

    if fields.get("requires-python"):
        project["requires-python"] = fields["requires-python"]

    if fields.get("license"):
        project["license"] = fields["license"]

    if fields.get("authors"):
        project["authors"] = fields["authors"]

    if fields.get("keywords"):
        project["keywords"] = fields["keywords"]

    if fields.get("classifiers"):
        project["classifiers"] = fields["classifiers"]

    if meta["dependencies"]:
        project["dependencies"] = meta["dependencies"]

    if fields.get("urls"):
        project["urls"] = fields["urls"]

    if meta["optional_deps"]:
        project["optional-dependencies"] = meta["optional_deps"]

    # Build the full pyproject structure
    pyproject = {
        "build-system": {
            "requires": ["rind"],
            "build-backend": "rind",
        },
        "project": project,
    }

    # Add tool.rind section with core-package for reference
    if meta.get("core_package"):
        pyproject["tool"] = {"rind": {"core-package": meta["core_package"]}}

    return tomli_w.dumps(pyproject)


def build_sdist(sdist_directory, config_settings=None):
    """Build a source distribution with resolved metadata.

    The sdist contains a transformed pyproject.toml with all metadata
    resolved and hardcoded, so that wheels can be built from sdists
    without access to the core pyproject.toml or git tags.
    """
    import tarfile

    # Get the original pyproject for reference
    original_pyproject = parse_pyproject()

    meta = build_metadata(config_settings)
    name = meta["name"]
    version = meta["version"]
    description = meta["metadata_fields"].get("description", "")

    # Generate resolved pyproject.toml
    resolved_pyproject = _generate_resolved_pyproject(meta, original_pyproject)

    # sdist filename uses underscores per PEP 625
    sdist_name = f"{safe_name(name)}-{version}"
    sdist_path = Path(sdist_directory) / f"{sdist_name}.tar.gz"

    with tarfile.open(sdist_path, "w:gz") as tar:
        # Include the resolved pyproject.toml
        pyproject_bytes = resolved_pyproject.encode("utf-8")
        info = tarfile.TarInfo(f"{sdist_name}/pyproject.toml")
        info.size = len(pyproject_bytes)
        tar.addfile(info, io.BytesIO(pyproject_bytes))

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

    return sdist_path.name
