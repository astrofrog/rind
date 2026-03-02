"""Tests for standalone mode (no core package)."""

import os
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path


class TestStandaloneMode:
    """Tests for standalone metapackages without a core package."""

    def test_build_metadata(self, temp_project_standalone):
        """Test that metadata is read from [project] in standalone mode."""
        from rind._metadata import build_metadata

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_standalone)
            meta = build_metadata()

            assert meta["name"] == "my-data-science-stack"
            assert meta["version"] == "1.0.0"
            assert meta["metadata_fields"]["description"] == (
                "A curated collection of data science packages"
            )
            assert meta["metadata_fields"]["requires-python"] == ">=3.9"
            assert "pandas>=2.0" in meta["dependencies"]
            assert "numpy>=1.24" in meta["dependencies"]
            assert "ml" in meta["optional_deps"]
            # No core package in standalone mode
            assert meta["core_package"] is None
        finally:
            os.chdir(original_cwd)

    def test_build_wheel(self, temp_project_standalone):
        """Test wheel build in standalone mode."""
        import rind

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_standalone)
            with tempfile.TemporaryDirectory() as wheel_dir:
                wheel_name = rind.build_wheel(wheel_dir)
                wheel_path = Path(wheel_dir) / wheel_name

                assert wheel_path.exists()
                assert "my_data_science_stack-1.0.0" in wheel_name

                with zipfile.ZipFile(wheel_path) as whl:
                    for name in whl.namelist():
                        if "METADATA" in name:
                            metadata = whl.read(name).decode("utf-8")
                            break

                assert "Name: my-data-science-stack" in metadata
                assert "Version: 1.0.0" in metadata
                assert "Requires-Dist: pandas>=2.0" in metadata
                assert "Requires-Dist: numpy>=1.24" in metadata
                assert "Requires-Dist: matplotlib>=3.7" in metadata
                assert "Provides-Extra: ml" in metadata
        finally:
            os.chdir(original_cwd)

    def test_build_sdist(self, temp_project_standalone):
        """Test sdist build in standalone mode."""
        import rind

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_standalone)
            with tempfile.TemporaryDirectory() as sdist_dir:
                sdist_name = rind.build_sdist(sdist_dir)
                sdist_path = Path(sdist_dir) / sdist_name

                assert sdist_path.exists()
                assert "my_data_science_stack-1.0.0" in sdist_name

                with tarfile.open(sdist_path, "r:gz") as tar:
                    names = tar.getnames()
                    assert any("pyproject.toml" in n for n in names)
                    assert any("PKG-INFO" in n for n in names)
        finally:
            os.chdir(original_cwd)

    def test_get_requires_for_build_wheel(self, temp_project_standalone):
        """Test build requirements for wheel in standalone mode."""
        import rind

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_standalone)
            reqs = rind.get_requires_for_build_wheel()
            # Standalone mode needs no extra deps - version is static
            assert reqs == []
        finally:
            os.chdir(original_cwd)

    def test_get_requires_for_build_sdist(self, temp_project_standalone):
        """Test build requirements for sdist in standalone mode."""
        import rind

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_standalone)
            reqs = rind.get_requires_for_build_sdist()
            # Standalone mode needs no extra deps - version is static
            assert reqs == []
        finally:
            os.chdir(original_cwd)

    def test_sdist_then_wheel(self, temp_project_standalone):
        """Test building wheel from sdist in standalone mode."""
        import rind
        from rind._metadata import build_metadata

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_standalone)

            # Build sdist
            with tempfile.TemporaryDirectory() as sdist_dir:
                sdist_name = rind.build_sdist(sdist_dir)
                sdist_path = Path(sdist_dir) / sdist_name

                # Extract sdist
                extract_dir = temp_project_standalone / "extracted"
                with tarfile.open(sdist_path, "r:gz") as tar:
                    if sys.version_info >= (3, 12):
                        tar.extractall(extract_dir, filter="data")
                    else:
                        tar.extractall(extract_dir)

                extracted = list(extract_dir.iterdir())[0]

                # Build wheel from extracted sdist
                os.chdir(extracted)

                # Verify metadata still works
                meta = build_metadata()
                assert meta["version"] == "1.0.0"
                assert "pandas>=2.0" in meta["dependencies"]

                # Build wheel
                with tempfile.TemporaryDirectory() as wheel_dir:
                    wheel_name = rind.build_wheel(wheel_dir)
                    assert "1.0.0" in wheel_name
        finally:
            os.chdir(original_cwd)

    def test_sdist_no_core_package_in_tool_rind(self, temp_project_standalone):
        """Test that sdist doesn't have core-package in [tool.rind]."""
        import rind
        from rind._utils import parse_pyproject

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_standalone)

            with tempfile.TemporaryDirectory() as sdist_dir:
                sdist_name = rind.build_sdist(sdist_dir)
                sdist_path = Path(sdist_dir) / sdist_name

                # Extract and check pyproject.toml
                extract_dir = temp_project_standalone / "extracted"
                with tarfile.open(sdist_path, "r:gz") as tar:
                    if sys.version_info >= (3, 12):
                        tar.extractall(extract_dir, filter="data")
                    else:
                        tar.extractall(extract_dir)

                extracted = list(extract_dir.iterdir())[0]
                pyproject = parse_pyproject(extracted / "pyproject.toml")

                # Should not have [tool.rind] at all in standalone mode
                assert "tool" not in pyproject or "rind" not in pyproject.get(
                    "tool", {}
                )
        finally:
            os.chdir(original_cwd)
