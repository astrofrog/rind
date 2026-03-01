"""
Metadata building logic for rind.
"""

import json
from pathlib import Path

from ._utils import get_core_pyproject_path, parse_pyproject

# This file is included in the sdist to cache build info,
# allowing wheels to be built from sdists without the parent pyproject.toml
CACHED_BUILD_INFO_FILE = ".rind_cache.json"


def load_cached_build_info():
    """Load cached build info from sdist (if present).

    Returns:
        dict or None: Cached build info, or None if not present
    """
    cache_path = Path(CACHED_BUILD_INFO_FILE)
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)
    return None


def save_build_info(version, core_project, dest_dir="."):
    """Save build info to cache file for inclusion in sdist.

    Args:
        version: The determined version string
        core_project: The core package's [project] section
        dest_dir: Directory to save the cache file

    Returns:
        Path: Path to the cache file
    """
    cache_path = Path(dest_dir) / CACHED_BUILD_INFO_FILE
    cache_data = {
        "version": version,
        "core_project": core_project,
    }
    with open(cache_path, "w") as f:
        json.dump(cache_data, f, indent=2)
    return cache_path


def build_metadata(config_settings=None):
    """Build and return all metadata needed for the package."""
    pyproject = parse_pyproject()
    tool_config = pyproject.get("tool", {}).get("rind", {})
    local_project = pyproject.get("project", {})

    # Check for cached build info (present when building wheel from sdist)
    cached = load_cached_build_info()

    if cached:
        # Building from sdist - use cached info
        version = cached["version"]
        core_project = cached["core_project"]
    else:
        # Building from source - read core pyproject.toml
        core_path = get_core_pyproject_path(tool_config)
        core_pyproject = parse_pyproject(core_path)
        core_project = core_pyproject.get("project", {})
        core_dir = core_path.parent

        # Get version using the appropriate strategy for the core package
        from ._version_helpers import get_version

        version = get_version(core_pyproject, core_dir)

    # Determine if we should inherit metadata (default: true)
    inherit_metadata = tool_config.get("inherit-metadata", True)

    # Get inherited values (empty dict if inherit-metadata is false)
    inherited = core_project if inherit_metadata else {}

    # Name is required - check tool.rind first, then [project]
    name = tool_config.get("name") or local_project.get("name")
    if not name:
        raise ValueError(
            "Package name must be specified in [tool.rind] name = ... "
            "or [project] name = ..."
        )

    # Get core package name from the core's pyproject.toml
    core_package = core_project.get("name")
    if not core_package:
        raise ValueError(
            "Could not determine core package name. Ensure the core package's "
            "pyproject.toml has [project] name = ..."
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
    # with the same pinned version. Use ["*"] to pass through all extras
    # from the core package.
    optional_deps = {}
    passthrough_extras = tool_config.get("passthrough-extras", [])
    if passthrough_extras == ["*"]:
        # Pass through all extras from core's optional-dependencies
        core_optional = core_project.get("optional-dependencies", {})
        passthrough_extras = list(core_optional.keys())
    for extra_name in passthrough_extras:
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
        "core_project": core_project,
    }
