"""Tests for rind."""

import os
import subprocess
import tarfile
import tempfile
import zipfile
from pathlib import Path

import pytest

# Sample pyproject.toml content for a core package using setuptools_scm
CORE_PYPROJECT = """\
[project]
name = "mypackage-core"
description = "My package core"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Test Author", email = "test@example.com"}
]
dynamic = ["version"]

[project.urls]
Homepage = "https://example.com"

[project.optional-dependencies]
extra1 = ["dep1>=1.0"]
extra2 = ["dep2>=2.0"]
test = ["pytest>=7.0"]
docs = ["sphinx>=7.0"]

[build-system]
requires = ["setuptools>=61", "setuptools_scm>=8"]
build-backend = "setuptools.build_meta"

[tool.setuptools_scm]
"""

# Sample pyproject.toml content for a core package with static version
CORE_PYPROJECT_STATIC = """\
[project]
name = "mypackage-core"
version = "2.0.0"
description = "My package core with static version"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Test Author", email = "test@example.com"}
]

[project.urls]
Homepage = "https://example.com"

[project.optional-dependencies]
extra1 = ["dep1>=1.0"]

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"
"""

# Sample pyproject.toml content for a metapackage
META_PYPROJECT = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
name = "mypackage"
description = "My package with batteries"
include-extras = ["extra1", "extra2"]
passthrough-extras = ["test", "docs"]
"""

META_PYPROJECT_NO_INHERIT = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[project]
name = "mypackage"
description = "Custom description"
requires-python = ">=3.10"

[tool.rind]
core-path = "../core"
inherit-metadata = false
include-extras = ["extra1"]
"""

META_PYPROJECT_WILDCARD = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
name = "mypackage"
include-extras = ["extra1", "extra2"]
passthrough-extras = ["*"]
"""

META_PYPROJECT_STATIC = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
name = "mypackage"
include-extras = ["extra1"]
"""


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure with setuptools_scm."""
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
def temp_project_static(tmp_path):
    """Create a temporary project structure with static version."""
    # Create core package pyproject.toml with static version
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT_STATIC)

    # Create meta package pyproject.toml
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT_STATIC)

    return tmp_path


@pytest.fixture
def temp_project_no_inherit(tmp_path):
    """Create a project with inherit-metadata = false."""
    # Create core package pyproject.toml
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT)

    # Create meta package pyproject.toml
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT_NO_INHERIT)

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
def temp_project_wildcard(tmp_path):
    """Create a project with wildcard passthrough-extras."""
    # Create core package pyproject.toml
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT)

    # Create meta package pyproject.toml with wildcard passthrough
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT_WILDCARD)

    # Initialize git repo
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Initial"], cwd=tmp_path, check=True)
    subprocess.run(["git", "tag", "v1.2.3"], cwd=tmp_path, check=True)

    return tmp_path


class TestBuildMetadata:
    """Tests for _build_metadata function."""

    def test_inherits_metadata(self, temp_project):
        """Test that metadata is inherited from core pyproject.toml."""
        from rind._metadata import build_metadata

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            assert meta["name"] == "mypackage"
            assert meta["version"] == "1.2.3"
            assert meta["core_package"] == "mypackage-core"
            assert meta["metadata_fields"]["requires-python"] == ">=3.9"
            assert meta["metadata_fields"]["license"] == {"text": "MIT"}
            # Description is overridden
            assert meta["metadata_fields"]["description"] == "My package with batteries"
        finally:
            os.chdir(original_cwd)

    def test_static_version(self, temp_project_static):
        """Test that static version is read correctly."""
        from rind._metadata import build_metadata

        meta_dir = temp_project_static / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            assert meta["version"] == "2.0.0"
            assert meta["core_package"] == "mypackage-core"
            assert "mypackage-core[extra1]==2.0.0" in meta["dependencies"][0]
        finally:
            os.chdir(original_cwd)

    def test_no_inherit_metadata(self, temp_project_no_inherit):
        """Test that inherit-metadata = false prevents inheritance."""
        from rind._metadata import build_metadata

        meta_dir = temp_project_no_inherit / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            assert meta["name"] == "mypackage"
            # Should use local [project] values, not inherited
            assert meta["metadata_fields"]["description"] == "Custom description"
            assert meta["metadata_fields"]["requires-python"] == ">=3.10"
            # License should be None since not inherited and not in local
            assert meta["metadata_fields"]["license"] is None
        finally:
            os.chdir(original_cwd)

    def test_core_extras(self, temp_project):
        """Test that include-extras are included in dependencies."""
        from rind._metadata import build_metadata

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            deps = meta["dependencies"]
            assert len(deps) == 1
            assert "mypackage-core[extra1,extra2]==1.2.3" in deps[0]
        finally:
            os.chdir(original_cwd)

    def test_passthrough_extras(self, temp_project):
        """Test that passthrough-extras are exposed."""
        from rind._metadata import build_metadata

        meta_dir = temp_project / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            optional = meta["optional_deps"]
            assert "test" in optional
            assert "docs" in optional
            assert "mypackage-core[test]==1.2.3" in optional["test"][0]
            assert "mypackage-core[docs]==1.2.3" in optional["docs"][0]
        finally:
            os.chdir(original_cwd)

    def test_passthrough_extras_wildcard(self, temp_project_wildcard):
        """Test that passthrough-extras = ['*'] passes through all extras."""
        from rind._metadata import build_metadata

        meta_dir = temp_project_wildcard / "meta"
        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            meta = build_metadata()

            optional = meta["optional_deps"]
            # Should have all 4 extras from core package
            assert "extra1" in optional
            assert "extra2" in optional
            assert "test" in optional
            assert "docs" in optional
            assert "mypackage-core[extra1]==1.2.3" in optional["extra1"][0]
            assert "mypackage-core[test]==1.2.3" in optional["test"][0]
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
                    # Should contain pyproject.toml and cached build info
                    assert any("pyproject.toml" in n for n in names)
                    assert any(".rind_cache.json" in n for n in names)
                    assert any("PKG-INFO" in n for n in names)
        finally:
            os.chdir(original_cwd)

    def test_sdist_build_info_cache(self, temp_project):
        """Test that build info (version + metadata) is cached in sdist."""
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
                        if ".rind_cache.json" in member.name:
                            f = tar.extractfile(member)
                            cached = json.load(f)
                            break

                # Check version is cached
                assert cached["version"] == "1.2.3"
                # Check core project metadata is cached
                assert cached["core_project"]["name"] == "mypackage-core"
                assert cached["core_project"]["description"] == "My package core"
                assert cached["core_project"]["requires-python"] == ">=3.9"
        finally:
            os.chdir(original_cwd)


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


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_safe_name(self):
        """Test wheel-safe name generation."""
        from rind._utils import safe_name

        assert safe_name("My_Package") == "my_package"
        assert safe_name("my.package") == "my_package"
        assert safe_name("my--package") == "my_package"

    def test_wheel_name(self):
        """Test wheel filename generation."""
        from rind._utils import wheel_name

        name = wheel_name("my-package", "1.2.3")
        assert name == "my_package-1.2.3-py3-none-any.whl"

    def test_record_hash(self):
        """Test RECORD hash generation."""
        from rind._utils import record_hash

        data = b"test content"
        hash_str = record_hash(data)
        assert hash_str.startswith("sha256=")
        # Should be consistent
        assert record_hash(data) == hash_str


class TestErrorHandling:
    """Tests for error handling."""

    def test_missing_core_path(self, tmp_path):
        """Test error when core-path is not specified."""
        from rind._metadata import build_metadata

        meta_dir = tmp_path / "meta"
        meta_dir.mkdir()
        (meta_dir / "pyproject.toml").write_text("""\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
name = "mypackage"
""")

        original_cwd = os.getcwd()
        try:
            os.chdir(meta_dir)
            with pytest.raises(ValueError, match="core-path is required"):
                build_metadata()
        finally:
            os.chdir(original_cwd)

    def test_missing_name(self, tmp_path):
        """Test error when name is not specified."""
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
