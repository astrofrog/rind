"""Integration tests that build a real metapackage using rind."""

import subprocess
import sys
import zipfile

import pytest

CORE_PYPROJECT = """\
[project]
name = "test-core"
description = "Test core package"
requires-python = ">=3.9"
authors = [{name = "Test"}]

[project.optional-dependencies]
recommended = ["requests"]
test = ["pytest"]
"""

META_PYPROJECT = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
inherit-metadata = "../core/pyproject.toml"
name = "test-meta"
include-extras = ["recommended"]
passthrough-extras = ["test"]
"""


@pytest.fixture
def integration_project(tmp_path):
    """Create a full project structure for integration testing."""
    # Create core package
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT)

    # Create meta package
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT)

    # Initialize git repo
    subprocess.run(
        ["git", "init", "-q"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "add", "-A"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "-m", "Initial"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "tag", "v1.0.0"],
        cwd=tmp_path,
        check=True,
    )

    return tmp_path


def test_build_meta_package(integration_project):
    """Test building a metapackage with python -m build."""
    meta_dir = integration_project / "meta"

    # Build the metapackage
    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=meta_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"

    # Find the built wheel
    dist_dir = meta_dir / "dist"
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1, f"Expected 1 wheel, found {len(wheels)}"

    wheel_path = wheels[0]
    assert "test_meta-1.0.0" in wheel_path.name

    # Verify wheel contents
    with zipfile.ZipFile(wheel_path) as whl:
        names = whl.namelist()

        # Should only have .dist-info files (no Python code)
        assert all(".dist-info/" in n for n in names)

        # Read and verify METADATA
        metadata_file = [n for n in names if n.endswith("METADATA")][0]
        metadata = whl.read(metadata_file).decode("utf-8")

        assert "Name: test-meta" in metadata
        assert "Version: 1.0.0" in metadata
        assert "Requires-Dist: test-core[recommended]==1.0.0" in metadata
        assert "Provides-Extra: test" in metadata
        assert "Requires-Dist: test-core[test]==1.0.0; extra == 'test'" in metadata
        assert "Requires-Python: >=3.9" in metadata


def test_build_sdist_then_wheel(integration_project):
    """Test building wheel from sdist (simulates PyPI install)."""
    meta_dir = integration_project / "meta"

    # Build sdist first
    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--sdist"],
        cwd=meta_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"sdist build failed: {result.stderr}"

    # Find the sdist
    dist_dir = meta_dir / "dist"
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(sdists) == 1

    # Extract sdist to a new location (simulating pip download)
    import tarfile

    extract_dir = integration_project / "sdist_extract"
    with tarfile.open(sdists[0], "r:gz") as tar:
        tar.extractall(extract_dir, filter="data")

    # Find extracted directory
    extracted = list(extract_dir.iterdir())[0]

    # Build wheel from extracted sdist (no access to parent pyproject.toml)
    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--wheel"],
        cwd=extracted,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Wheel build from sdist failed: {result.stderr}"

    # Verify the wheel has correct metadata
    wheels = list((extracted / "dist").glob("*.whl"))
    assert len(wheels) == 1

    with zipfile.ZipFile(wheels[0]) as whl:
        metadata_file = [n for n in whl.namelist() if n.endswith("METADATA")][0]
        metadata = whl.read(metadata_file).decode("utf-8")

        # Should have inherited metadata even though built from sdist
        assert "Requires-Python: >=3.9" in metadata
        assert "Requires-Dist: test-core[recommended]==1.0.0" in metadata
