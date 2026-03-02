"""Tests for rind._version_helpers module."""

from pathlib import Path

import pytest


class TestVersionHelpers:
    """Tests for version detection helpers."""

    def test_static_version_detection(self):
        """Test detection of static version."""
        from rind._version_helpers import _has_static_version

        # Static version
        assert _has_static_version({"project": {"version": "1.0.0"}})

        # Dynamic version
        assert not _has_static_version(
            {"project": {"version": "1.0.0", "dynamic": ["version"]}}
        )

        # No version
        assert not _has_static_version({"project": {}})

    def test_setuptools_scm_detection(self):
        """Test detection of setuptools_scm usage."""
        from rind._version_helpers import _uses_setuptools_scm

        # In build requirements
        assert _uses_setuptools_scm(
            {"build-system": {"requires": ["setuptools_scm>=8"]}}
        )
        assert _uses_setuptools_scm(
            {"build-system": {"requires": ["setuptools-scm>=8"]}}
        )

        # In tool config
        assert _uses_setuptools_scm({"tool": {"setuptools_scm": {}}})

        # hatch-vcs
        assert _uses_setuptools_scm({"build-system": {"requires": ["hatch-vcs"]}})
        assert _uses_setuptools_scm({"tool": {"hatch": {"version": {"source": "vcs"}}}})

        # Not using it
        assert not _uses_setuptools_scm({"build-system": {"requires": ["setuptools"]}})

    def test_version_requires_static(self):
        """Test that static version requires no deps."""
        from rind._version_helpers import get_version_requires

        reqs = get_version_requires({"project": {"version": "1.0.0"}})
        assert reqs == []

    def test_version_requires_scm(self):
        """Test that setuptools_scm version requires setuptools_scm."""
        from rind._version_helpers import get_version_requires

        reqs = get_version_requires(
            {
                "project": {"dynamic": ["version"]},
                "build-system": {"requires": ["setuptools_scm>=8"]},
            }
        )
        assert "setuptools_scm>=8.0" in reqs

    def test_version_requires_fallback(self):
        """Test that unknown backend requires pyproject_hooks + build deps."""
        from rind._version_helpers import get_version_requires

        reqs = get_version_requires(
            {
                "project": {"dynamic": ["version"]},
                "build-system": {
                    "requires": ["flit_core>=3.0"],
                    "build-backend": "flit_core.buildapi",
                },
            }
        )
        assert "pyproject_hooks" in reqs
        assert "flit_core>=3.0" in reqs

    def test_get_version_via_backend_no_backend(self):
        """Test error when build-backend is not specified."""
        from rind._version_helpers import _get_version_via_backend

        with pytest.raises(ValueError, match="no build-backend specified"):
            _get_version_via_backend(Path("."), {})
