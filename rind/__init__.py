"""
rind: A minimal PEP 517 build backend for meta-packages.

See https://rind.readthedocs.io for documentation.
"""

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0"

# PEP 517 build backend hooks
from ._backend import (
    build_sdist,
    build_wheel,
    get_requires_for_build_sdist,
    get_requires_for_build_wheel,
)

__all__ = [
    "__version__",
    "build_wheel",
    "build_sdist",
    "get_requires_for_build_wheel",
    "get_requires_for_build_sdist",
]
