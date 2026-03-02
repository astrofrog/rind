"""Tests for error handling across rind modules."""

import os

import pytest


class TestErrorHandling:
    """Tests for error handling."""

    def test_sdist_mode_missing_version(self, tmp_path):
        """Test error when in sdist mode but version is not in [project]."""
        from rind._metadata import build_metadata

        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()
        # No core-path means sdist mode, which requires version in [project]
        (meta_dir / "pyproject.toml").write_text("""\
[build-system]
requires = ["rind"]
build-backend = "rind"

[project]
name = "mypackage"
""")

        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with pytest.raises(ValueError, match="Version must be specified"):
                build_metadata()
        finally:
            os.chdir(original_cwd)

    def test_sdist_mode_missing_name(self, tmp_path):
        """Test error when in sdist mode but name is not in [project]."""
        from rind._metadata import build_metadata

        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()
        # No core-path means sdist mode, which requires name in [project]
        (meta_dir / "pyproject.toml").write_text("""\
[build-system]
requires = ["rind"]
build-backend = "rind"

[project]
version = "1.0.0"
""")

        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with pytest.raises(ValueError, match="Package name must be specified"):
                build_metadata()
        finally:
            os.chdir(original_cwd)

    def test_get_core_pyproject_path_missing(self, tmp_path):
        """Test error when core-path is not specified."""
        from rind._utils import get_core_pyproject_path

        with pytest.raises(ValueError, match="core-path is required"):
            get_core_pyproject_path({})

    def test_missing_name(self, tmp_path):
        """Test error when metapackage name is not specified."""
        from rind._metadata import build_metadata

        # Create core package without name
        core_dir = tmp_path / "core"
        core_dir.mkdir()
        (core_dir / "pyproject.toml").write_text("""\
[project]
version = "1.0.0"

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
""")

        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()
        (meta_dir / "pyproject.toml").write_text("""\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
""")

        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with pytest.raises(ValueError, match="Package name must be specified"):
                build_metadata()
        finally:
            os.chdir(original_cwd)

    def test_missing_core_package_name(self, tmp_path):
        """Test error when core package name is not specified."""
        from rind._metadata import build_metadata

        # Create core package without name in [project]
        core_dir = tmp_path / "core"
        core_dir.mkdir()
        (core_dir / "pyproject.toml").write_text("""\
[project]
version = "1.0.0"

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
""")

        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()
        (meta_dir / "pyproject.toml").write_text("""\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
name = "mypackage"
""")

        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with pytest.raises(
                ValueError, match="Could not determine core package name"
            ):
                build_metadata()
        finally:
            os.chdir(original_cwd)
