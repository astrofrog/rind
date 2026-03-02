"""
Metadata building logic for rind.
"""

from ._utils import get_core_pyproject_path, parse_pyproject


def build_metadata(config_settings=None):
    """Build and return all metadata needed for the package.

    This function operates in two modes:
    1. Source mode: core-path is specified, compute everything from core package
    2. Sdist mode: no core-path, read resolved values from [project] directly
    """
    pyproject = parse_pyproject()
    tool_config = pyproject.get("tool", {}).get("rind", {})
    local_project = pyproject.get("project", {})

    # Check if we're in source mode (core-path present) or sdist mode (no core-path)
    core_path_config = tool_config.get("core-path")

    if core_path_config:
        # Source mode: compute everything from core package
        return _build_metadata_from_source(pyproject, tool_config, local_project)
    else:
        # Sdist mode: read resolved values from [project]
        return _build_metadata_from_resolved(pyproject, tool_config, local_project)


def _build_metadata_from_source(pyproject, tool_config, local_project):
    """Build metadata by reading from core package (source mode)."""
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

    dependencies = [core_dep]

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
    }


def _build_metadata_from_resolved(pyproject, tool_config, local_project):
    """Build metadata from resolved [project] values (sdist mode)."""
    # In sdist mode, everything is already in [project]
    name = local_project.get("name")
    if not name:
        raise ValueError("Package name must be specified in [project] name = ...")

    version = local_project.get("version")
    if not version:
        raise ValueError("Version must be specified in [project] version = ...")

    # Read dependencies directly
    dependencies = local_project.get("dependencies", [])

    # Read optional dependencies directly
    optional_deps = local_project.get("optional-dependencies", {})

    # Read metadata fields directly from [project]
    metadata_fields = {
        "description": local_project.get("description"),
        "requires-python": local_project.get("requires-python"),
        "license": local_project.get("license"),
        "authors": local_project.get("authors"),
        "urls": local_project.get("urls"),
        "classifiers": local_project.get("classifiers"),
        "keywords": local_project.get("keywords"),
    }

    # Core package name is stored in tool.rind for reference
    core_package = tool_config.get("core-package")

    return {
        "name": name,
        "version": version,
        "metadata_fields": metadata_fields,
        "dependencies": dependencies,
        "optional_deps": optional_deps,
        "core_package": core_package,
    }
