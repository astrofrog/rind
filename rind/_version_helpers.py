"""
Version detection helpers for rind.

Supports multiple versioning strategies based on the core package's build system:
1. Static version in pyproject.toml - just read it directly
2. setuptools_scm / hatch-vcs - use setuptools_scm (fast, direct)
3. Generic fallback - call core's PEP 517 backend via pyproject_hooks
"""

import tempfile
from pathlib import Path


def _has_static_version(pyproject):
    """Check if version is statically defined (not dynamic)."""
    project = pyproject.get("project", {})
    return "version" in project and "version" not in project.get("dynamic", [])


def _uses_setuptools_scm(pyproject):
    """Check if the project uses setuptools_scm or hatch-vcs."""
    build_requires = pyproject.get("build-system", {}).get("requires", [])

    for req in build_requires:
        req_lower = req.lower().replace("-", "_")
        if "setuptools_scm" in req_lower:
            return True
        if "hatch_vcs" in req_lower:
            return True

    # Also check tool config
    tool = pyproject.get("tool", {})
    if "setuptools_scm" in tool:
        return True
    return tool.get("hatch", {}).get("version", {}).get("source") == "vcs"


def get_version_requires(core_pyproject):
    """
    Get build requirements needed to determine the version.

    Args:
        core_pyproject: Parsed core pyproject.toml dict

    Returns:
        list: Build requirement strings
    """
    if _has_static_version(core_pyproject):
        return []

    if _uses_setuptools_scm(core_pyproject):
        return ["setuptools_scm>=8.0"]

    # Fallback: need pyproject_hooks + core's build requirements
    core_requires = core_pyproject.get("build-system", {}).get("requires", [])
    return ["pyproject_hooks"] + list(core_requires)


def get_version(core_pyproject, core_dir):
    """
    Get the version of the core package.

    Args:
        core_pyproject: Parsed core pyproject.toml dict
        core_dir: Path to core package directory (where pyproject.toml lives)

    Returns:
        str: Version string
    """
    # Strategy 1: Static version - just read it
    if _has_static_version(core_pyproject):
        return core_pyproject["project"]["version"]

    # Strategy 2: setuptools_scm / hatch-vcs - use setuptools_scm directly
    if _uses_setuptools_scm(core_pyproject):
        from setuptools_scm import get_version as scm_get_version

        return scm_get_version(root=str(core_dir), search_parent_directories=True)

    # Strategy 3: Call the core's build backend via pyproject_hooks
    return _get_version_via_backend(core_dir, core_pyproject.get("build-system", {}))


def _get_version_via_backend(core_dir, build_system):
    """
    Get version by calling the core's PEP 517 backend.

    This is the most general approach - it works with any PEP 517 compliant
    backend by calling prepare_metadata_for_build_wheel and parsing the result.

    Args:
        core_dir: Path to core package directory
        build_system: The build-system table from pyproject.toml

    Returns:
        str: Version string

    Raises:
        ValueError: If no build-backend is specified
    """
    from email.parser import Parser

    from pyproject_hooks import BuildBackendHookCaller

    backend = build_system.get("build-backend")
    if not backend:
        raise ValueError("Core package has no build-backend specified")

    hooks = BuildBackendHookCaller(
        source_dir=str(core_dir),
        build_backend=backend,
        backend_path=build_system.get("backend-path", []),
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        dist_info_name = hooks.prepare_metadata_for_build_wheel(tmpdir)
        metadata_path = Path(tmpdir) / dist_info_name / "METADATA"
        with open(metadata_path) as f:
            msg = Parser().parse(f)
        return msg["Version"]
