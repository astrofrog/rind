"""
Utility functions for rind.
"""

import hashlib
import sys
from base64 import urlsafe_b64encode
from pathlib import Path

from packaging.utils import canonicalize_name

# tomllib is built-in from Python 3.11+, use tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def get_rind_version():
    """Get rind's own version for the wheel generator tag."""
    try:
        from ._version import version

        return version
    except ImportError:
        return "0.0.0"


def safe_name(name):
    """Return wheel-safe name (lowercase, underscores).

    Uses PEP 503 normalization, then replaces hyphens with underscores
    for wheel/sdist filenames per PEP 427.
    """
    return canonicalize_name(name).replace("-", "_")


def wheel_name(name, version):
    """Generate wheel filename per PEP 427."""
    return f"{safe_name(name)}-{version}-py3-none-any.whl"


def parse_pyproject(path="pyproject.toml"):
    """Parse pyproject.toml and return data."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def record_hash(data):
    """Calculate hash for RECORD file.

    RECORD uses base64url-encoded sha256 without padding.
    """
    digest = hashlib.sha256(data).digest()
    hash_str = urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return f"sha256={hash_str}"


def get_core_pyproject_path(tool_config):
    """Get the path to the core package's pyproject.toml.

    Args:
        tool_config: The [tool.rind] configuration dict

    Returns:
        Path: Resolved path to core's pyproject.toml

    Raises:
        ValueError: If core-path is not specified
    """
    core_path = tool_config.get("core-path")
    if not core_path:
        raise ValueError(
            "[tool.rind] core-path is required. "
            "Set it to the directory containing your core package, "
            'e.g., core-path = ".."'
        )
    return (Path.cwd() / core_path / "pyproject.toml").resolve()
