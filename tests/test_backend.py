"""Tests for rind."""

import os
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

import pytest

# Sample pyproject.toml content for a core package
CORE_PYPROJECT = """\
[project]
name = "mypackage-core"
description = "My package core"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Test Author", email = "test@example.com"}
]

[project.urls]
Homepage = "https://example.com"

[project.optional-dependencies]
extra1 = ["dep1>=1.0"]
extra2 = ["dep2>=2.0"]
test = ["pytest>=7.0"]
docs = ["sphinx>=7.0"]
"""

# Sample pyproject.toml content for a metapackage
META_PYPROJECT = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
inherit-metadata = "../core/pyproject.toml"
name = "mypackage"
description = "My package with batteries"
include-extras = ["extra1", "extra2"]
passthrough-extras = ["test", "docs"]
"""

META_PYPROJECT_MINIMAL = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
name = "mypackage"
core-package = "mypackage-core"
"""


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure."""
    # Create core package pyproject.toml
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT)

    # Create meta package pyproject.toml
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT)

    # Initialize git repo for version detection
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Initial"], cwd=tmp_path, check=True)
    subprocess.run(["git", "tag", "v1.2.3"], cwd=tmp_path, check=True)

    return tmp_path


@pytest.fixture
def temp_project_minimal(tmp_path):
    """Create a minimal project without inheritance."""
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT_MINIMAL)

    # Initialize git repo
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Initial"], cwd=tmp_path, check=True)
    subprocess.run(["git", "tag", "v0.1.0"], cwd=tmp_path, check=True)

    return tmp_path


class TestBuildMetadata:
    """Tests for _build_metadata function."""

    def test_inherits_metadata(self, temp_project):
        """Test that metadata is inherited from parent pyproject.toml."""
        from rind._backend import _build_metadata

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = _build_metadata()

            assert meta["name"] == "mypackage"
            assert meta["version"] == "1.2.3"
            assert meta["core_package"] == "mypackage-core"
            assert meta["metadata_fields"]["requires-python"] == ">=3.9"
            assert meta["metadata_fields"]["license"] == {"text": "MIT"}
            # Description is overridden
            assert meta["metadata_fields"]["description"] == "My package with batteries"
        finally:
            os.chdir(original_cwd)

    def test_core_extras(self, temp_project):
        """Test that include-extras are included in dependencies."""
        from rind._backend import _build_metadata

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = _build_metadata()

            deps = meta["dependencies"]
            assert len(deps) == 1
            assert "mypackage-core[extra1,extra2]==1.2.3" in deps[0]
        finally:
            os.chdir(original_cwd)

    def test_passthrough_extras(self, temp_project):
        """Test that passthrough-extras are exposed."""
        from rind._backend import _build_metadata

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = _build_metadata()

            optional = meta["optional_deps"]
            assert "test" in optional
            assert "docs" in optional
            assert "mypackage-core[test]==1.2.3" in optional["test"][0]
            assert "mypackage-core[docs]==1.2.3" in optional["docs"][0]
        finally:
            os.chdir(original_cwd)

    def test_minimal_config(self, temp_project_minimal):
        """Test minimal configuration without inheritance."""
        from rind._backend import _build_metadata

        meta_dir = temp_project_minimal / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = _build_metadata()

            assert meta["name"] == "mypackage"
            assert meta["version"] == "0.1.0"
            # Should default to {name}-core
            assert meta["core_package"] == "mypackage-core"
            assert "mypackage-core==0.1.0" in meta["dependencies"][0]
        finally:
            os.chdir(original_cwd)


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
                    # Should contain pyproject.toml and cached metadata
                    assert any("pyproject.toml" in n for n in names)
                    assert any(".rind_inherited.json" in n for n in names)
                    assert any("PKG-INFO" in n for n in names)
        finally:
            os.chdir(original_cwd)

    def test_sdist_inherited_cache(self, temp_project):
        """Test that inherited metadata is cached in sdist."""
        import json

        import rind

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with tempfile.TemporaryDirectory() as sdist_dir:
                sdist_name = rind.build_sdist(sdist_dir)
                sdist_path = Path(sdist_dir) / sdist_name

                with tarfile.open(sdist_path, "r:gz") as tar:
                    for member in tar.getmembers():
                        if ".rind_inherited.json" in member.name:
                            f = tar.extractfile(member)
                            cached = json.load(f)
                            break

                assert cached["name"] == "mypackage-core"
                assert cached["description"] == "My package core"
                assert cached["requires-python"] == ">=3.9"
        finally:
            os.chdir(original_cwd)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_safe_name(self):
        """Test wheel-safe name generation."""
        from rind._backend import _safe_name

        assert _safe_name("My_Package") == "my_package"
        assert _safe_name("my.package") == "my_package"
        assert _safe_name("my--package") == "my_package"

    def test_wheel_name(self):
        """Test wheel filename generation."""
        from rind._backend import _wheel_name

        name = _wheel_name("my-package", "1.2.3")
        assert name == "my_package-1.2.3-py3-none-any.whl"

    def test_record_hash(self):
        """Test RECORD hash generation."""
        from rind._backend import _record_hash

        data = b"test content"
        hash_str = _record_hash(data)
        assert hash_str.startswith("sha256=")
        # Should be consistent
        assert _record_hash(data) == hash_str


class TestGetRequires:
    """Tests for get_requires_for_build_* functions."""

    def test_get_requires_for_build_wheel(self):
        """Test build requirements for wheel."""
        import rind

        reqs = rind.get_requires_for_build_wheel()
        assert "setuptools_scm" in reqs

    def test_get_requires_for_build_sdist(self):
        """Test build requirements for sdist."""
        import rind

        reqs = rind.get_requires_for_build_sdist()
        assert "setuptools_scm" in reqs
