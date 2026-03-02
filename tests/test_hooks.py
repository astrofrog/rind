"""Tests for rind._hooks module."""

import os
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path


class TestBuildWheel:
    """Tests for build_wheel function."""

    def test_wheel_structure(self, temp_project):
        """Test that wheel contains only .dist-info."""
        import rind

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as wheel_dir:
                wheel_name = rind.build_wheel(wheel_dir)
                wheel_path = Path(wheel_dir) / wheel_name

                assert wheel_path.exists()
                assert wheel_name.endswith("-py3-none-any.whl")

                with zipfile.ZipFile(wheel_path) as whl:
                    names = whl.namelist()
                    # Should only have .dist-info files
                    assert all(".dist-info/" in n for n in names)
                    assert any("METADATA" in n for n in names)
                    assert any("WHEEL" in n for n in names)
                    assert any("RECORD" in n for n in names)
        finally:
            os.chdir(original_cwd)

    def test_wheel_metadata_content(self, temp_project):
        """Test that wheel METADATA has correct content."""
        import rind

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as wheel_dir:
                wheel_name = rind.build_wheel(wheel_dir)
                wheel_path = Path(wheel_dir) / wheel_name

                with zipfile.ZipFile(wheel_path) as whl:
                    for name in whl.namelist():
                        if "METADATA" in name:
                            metadata = whl.read(name).decode("utf-8")
                            break

                assert "Name: mypackage" in metadata
                assert "Version: 1.2.3" in metadata
                assert "Requires-Dist: mypackage-core[extra1,extra2]==1.2.3" in metadata
                assert "Requires-Python: >=3.9" in metadata
                assert "License: MIT" in metadata
                assert "Author: Test Author" in metadata
                assert "Provides-Extra: test" in metadata
                assert "Provides-Extra: docs" in metadata
        finally:
            os.chdir(original_cwd)

    def test_wheel_static_version(self, temp_project_static):
        """Test wheel build with static version (no git needed)."""
        import rind

        meta_dir = temp_project_static / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as wheel_dir:
                wheel_name = rind.build_wheel(wheel_dir)

                assert "2.0.0" in wheel_name
        finally:
            os.chdir(original_cwd)

    def test_wheel_full_metadata(self, temp_project_full_metadata):
        """Test wheel with string license, classifiers, and keywords list."""
        import rind

        meta_dir = temp_project_full_metadata / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as wheel_dir:
                wheel_name = rind.build_wheel(wheel_dir)
                wheel_path = Path(wheel_dir) / wheel_name

                with zipfile.ZipFile(wheel_path) as whl:
                    for name in whl.namelist():
                        if "METADATA" in name:
                            metadata = whl.read(name).decode("utf-8")
                            break

                # License as string (not dict)
                assert "License: MIT" in metadata
                # Classifiers
                assert "Classifier: Development Status :: 4 - Beta" in metadata
                assert "Classifier: License :: OSI Approved :: MIT License" in metadata
                # Keywords as list joined with comma
                assert "Keywords: test,package" in metadata
        finally:
            os.chdir(original_cwd)

    def test_wheel_keywords_string(self, temp_project_keywords_string):
        """Test wheel with keywords as comma-separated string."""
        import rind

        meta_dir = temp_project_keywords_string / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as wheel_dir:
                wheel_name = rind.build_wheel(wheel_dir)
                wheel_path = Path(wheel_dir) / wheel_name

                with zipfile.ZipFile(wheel_path) as whl:
                    for name in whl.namelist():
                        if "METADATA" in name:
                            metadata = whl.read(name).decode("utf-8")
                            break

                # Keywords kept as string
                assert "Keywords: test, package, example" in metadata
        finally:
            os.chdir(original_cwd)


class TestBuildSdist:
    """Tests for build_sdist function."""

    def test_sdist_structure(self, temp_project):
        """Test that sdist contains required files."""
        import rind

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as sdist_dir:
                sdist_name = rind.build_sdist(sdist_dir)
                sdist_path = Path(sdist_dir) / sdist_name

                assert sdist_path.exists()
                assert sdist_name.endswith(".tar.gz")

                with tarfile.open(sdist_path, "r:gz") as tar:
                    names = tar.getnames()
                    # Should contain resolved pyproject.toml and PKG-INFO
                    assert any("pyproject.toml" in n for n in names)
                    assert any("PKG-INFO" in n for n in names)
        finally:
            os.chdir(original_cwd)

    def test_sdist_resolved_pyproject(self, temp_project):
        """Test that sdist contains resolved pyproject.toml with all values."""
        import rind
        from rind._utils import parse_pyproject

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as sdist_dir:
                sdist_name = rind.build_sdist(sdist_dir)
                sdist_path = Path(sdist_dir) / sdist_name

                # Extract and parse the pyproject.toml
                extract_dir = meta_dir / "extracted"
                with tarfile.open(sdist_path, "r:gz") as tar:
                    if sys.version_info >= (3, 12):
                        tar.extractall(extract_dir, filter="data")
                    else:
                        tar.extractall(extract_dir)

                extracted = list(extract_dir.iterdir())[0]
                pyproject = parse_pyproject(extracted / "pyproject.toml")

                # Check resolved values
                assert pyproject["project"]["version"] == "1.2.3"
                assert pyproject["project"]["name"] == "mypackage"
                assert pyproject["project"]["requires-python"] == ">=3.9"
                assert pyproject["tool"]["rind"]["core-package"] == "mypackage-core"
                # Should have resolved dependencies
                assert (
                    "mypackage-core[extra1,extra2]==1.2.3"
                    in pyproject["project"]["dependencies"]
                )
                # Should NOT have core-path (that's only for source builds)
                assert "core-path" not in pyproject["tool"]["rind"]
        finally:
            os.chdir(original_cwd)

    def test_sdist_resolved_pyproject_full_metadata(self, temp_project_full_metadata):
        """Test sdist with string license, keywords, and classifiers."""
        import rind
        from rind._utils import parse_pyproject

        meta_dir = temp_project_full_metadata / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as sdist_dir:
                sdist_name = rind.build_sdist(sdist_dir)
                sdist_path = Path(sdist_dir) / sdist_name

                # Extract and parse the pyproject.toml
                extract_dir = meta_dir / "extracted"
                with tarfile.open(sdist_path, "r:gz") as tar:
                    if sys.version_info >= (3, 12):
                        tar.extractall(extract_dir, filter="data")
                    else:
                        tar.extractall(extract_dir)

                extracted = list(extract_dir.iterdir())[0]
                pyproject = parse_pyproject(extracted / "pyproject.toml")

                # String license (not dict)
                assert pyproject["project"]["license"] == "MIT"
                # Keywords as list
                assert pyproject["project"]["keywords"] == ["test", "package"]
                # Classifiers
                assert (
                    "Development Status :: 4 - Beta"
                    in pyproject["project"]["classifiers"]
                )
        finally:
            os.chdir(original_cwd)

    def test_sdist_resolved_pyproject_keywords_string(
        self, temp_project_keywords_string
    ):
        """Test sdist with keywords as comma-separated string."""
        import rind

        meta_dir = temp_project_keywords_string / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as sdist_dir:
                sdist_name = rind.build_sdist(sdist_dir)
                sdist_path = Path(sdist_dir) / sdist_name

                with tarfile.open(sdist_path, "r:gz") as tar:
                    for member in tar.getmembers():
                        if "pyproject.toml" in member.name:
                            f = tar.extractfile(member)
                            content = f.read().decode("utf-8")
                            break

                # Keywords as string (preserved as-is)
                assert 'keywords = "test, package, example"' in content
        finally:
            os.chdir(original_cwd)


class TestGetRequires:
    """Tests for get_requires_for_build_* functions."""

    def test_get_requires_for_build_wheel_scm(self, temp_project):
        """Test build requirements for wheel with setuptools_scm."""
        import rind

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            reqs = rind.get_requires_for_build_wheel()
            assert "setuptools_scm>=8.0" in reqs
        finally:
            os.chdir(original_cwd)

    def test_get_requires_for_build_wheel_from_sdist(self, temp_project_static):
        """Test build requirements for wheel when building from sdist (cached)."""
        import rind

        meta_dir = temp_project_static / "meta"
        original_cwd = os.getcwd()
        try:
            # Build sdist from the meta package
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as sdist_dir:
                sdist_name = rind.build_sdist(sdist_dir)
                sdist_path = Path(sdist_dir) / sdist_name

                # Extract sdist to a new location (simulating pip download)
                extract_dir = temp_project_static / "extracted_for_reqs"
                with tarfile.open(sdist_path, "r:gz") as tar:
                    if sys.version_info >= (3, 12):
                        tar.extractall(extract_dir, filter="data")
                    else:
                        tar.extractall(extract_dir)

                # Find the extracted directory
                extracted = list(extract_dir.iterdir())[0]

                # Call get_requires_for_build_wheel from within extracted sdist
                os.chdir(extracted)
                reqs = rind.get_requires_for_build_wheel()

                # When building from sdist with cached info, no deps needed
                assert reqs == []
        finally:
            os.chdir(original_cwd)

    def test_get_requires_for_build_wheel_static(self, temp_project_static):
        """Test build requirements for wheel with static version."""
        import rind

        meta_dir = temp_project_static / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            reqs = rind.get_requires_for_build_wheel()
            assert reqs == []
        finally:
            os.chdir(original_cwd)

    def test_get_requires_for_build_sdist(self, temp_project):
        """Test build requirements for sdist."""
        import rind

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            reqs = rind.get_requires_for_build_sdist()
            assert "setuptools_scm>=8.0" in reqs
        finally:
            os.chdir(original_cwd)
