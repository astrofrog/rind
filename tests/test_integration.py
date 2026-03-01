"""Integration tests that build a real metapackage using rind."""

import subprocess
import sys
import tarfile
import zipfile

import pytest

# =============================================================================
# Test fixtures for different versioning systems
# =============================================================================

# --- setuptools_scm ---

CORE_PYPROJECT_SETUPTOOLS_SCM = """\
[project]
name = "test-core"
description = "Test core package"
requires-python = ">=3.9"
authors = [{name = "Test"}]
dynamic = ["version"]

[project.optional-dependencies]
recommended = ["requests"]
test = ["pytest"]

[build-system]
requires = ["setuptools>=61", "setuptools_scm>=8"]
build-backend = "setuptools.build_meta"

[tool.setuptools_scm]
"""

META_PYPROJECT_SETUPTOOLS_SCM = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
name = "test-meta"
include-extras = ["recommended"]
passthrough-extras = ["test"]
"""

# --- hatch-vcs ---

CORE_PYPROJECT_HATCH_VCS = """\
[project]
name = "test-core"
description = "Test core package"
requires-python = ">=3.9"
authors = [{name = "Test"}]
dynamic = ["version"]

[project.optional-dependencies]
recommended = ["requests"]
test = ["pytest"]

[build-system]
requires = ["hatchling", "hatch-vcs"]
build-backend = "hatchling.build"

[tool.hatch.version]
source = "vcs"
"""

META_PYPROJECT_HATCH_VCS = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
name = "test-meta"
include-extras = ["recommended"]
passthrough-extras = ["test"]
"""

# --- static version ---

CORE_PYPROJECT_STATIC = """\
[project]
name = "test-core"
version = "2.5.0"
description = "Test core package"
requires-python = ">=3.9"
authors = [{name = "Test"}]

[project.optional-dependencies]
recommended = ["requests"]
test = ["pytest"]

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"
"""

META_PYPROJECT_STATIC = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
name = "test-meta"
include-extras = ["recommended"]
passthrough-extras = ["test"]
"""

# =============================================================================
# Fixtures
# =============================================================================


def _init_git_repo(tmp_path, tag="v1.0.0"):
    """Initialize a git repo with a tag."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Initial"], cwd=tmp_path, check=True)
    subprocess.run(["git", "tag", tag], cwd=tmp_path, check=True)


@pytest.fixture
def integration_project_setuptools_scm(tmp_path):
    """Create a project using setuptools_scm for versioning."""
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT_SETUPTOOLS_SCM)

    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT_SETUPTOOLS_SCM)

    _init_git_repo(tmp_path, "v1.0.0")
    return tmp_path


@pytest.fixture
def integration_project_hatch_vcs(tmp_path):
    """Create a project using hatch-vcs for versioning."""
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT_HATCH_VCS)

    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT_HATCH_VCS)

    _init_git_repo(tmp_path, "v1.0.0")
    return tmp_path


@pytest.fixture
def integration_project_static(tmp_path):
    """Create a project using static version."""
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT_STATIC)

    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT_STATIC)

    # No git needed for static version
    return tmp_path


# =============================================================================
# Tests for setuptools_scm versioning
# =============================================================================


def test_build_setuptools_scm(integration_project_setuptools_scm):
    """Test building a metapackage with setuptools_scm versioning."""
    meta_dir = integration_project_setuptools_scm / "meta"

    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=meta_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"

    dist_dir = meta_dir / "dist"
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    wheel_path = wheels[0]
    assert "test_meta-1.0.0" in wheel_path.name

    with zipfile.ZipFile(wheel_path) as whl:
        names = whl.namelist()
        assert all(".dist-info/" in n for n in names)

        metadata_file = [n for n in names if n.endswith("METADATA")][0]
        metadata = whl.read(metadata_file).decode("utf-8")

        assert "Name: test-meta" in metadata
        assert "Version: 1.0.0" in metadata
        assert "Requires-Dist: test-core[recommended]==1.0.0" in metadata
        assert "Provides-Extra: test" in metadata
        assert "Requires-Dist: test-core[test]==1.0.0; extra == 'test'" in metadata
        assert "Requires-Python: >=3.9" in metadata


def test_build_sdist_then_wheel_setuptools_scm(integration_project_setuptools_scm):
    """Test building wheel from sdist with setuptools_scm versioning."""
    meta_dir = integration_project_setuptools_scm / "meta"

    # Build sdist first
    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--sdist"],
        cwd=meta_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"sdist build failed: {result.stderr}"

    dist_dir = meta_dir / "dist"
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(sdists) == 1

    # Extract sdist to a new location (simulating pip download)
    extract_dir = integration_project_setuptools_scm / "sdist_extract"
    with tarfile.open(sdists[0], "r:gz") as tar:
        if sys.version_info >= (3, 12):
            tar.extractall(extract_dir, filter="data")
        else:
            tar.extractall(extract_dir)

    extracted = list(extract_dir.iterdir())[0]

    # Build wheel from extracted sdist (no access to core pyproject.toml)
    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--wheel"],
        cwd=extracted,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Wheel build from sdist failed: {result.stderr}"

    wheels = list((extracted / "dist").glob("*.whl"))
    assert len(wheels) == 1

    with zipfile.ZipFile(wheels[0]) as whl:
        metadata_file = [n for n in whl.namelist() if n.endswith("METADATA")][0]
        metadata = whl.read(metadata_file).decode("utf-8")

        assert "Requires-Python: >=3.9" in metadata
        assert "Requires-Dist: test-core[recommended]==1.0.0" in metadata


# =============================================================================
# Tests for hatch-vcs versioning
# =============================================================================


def test_build_hatch_vcs(integration_project_hatch_vcs):
    """Test building a metapackage with hatch-vcs versioning."""
    meta_dir = integration_project_hatch_vcs / "meta"

    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=meta_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"

    dist_dir = meta_dir / "dist"
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    wheel_path = wheels[0]
    assert "test_meta-1.0.0" in wheel_path.name

    with zipfile.ZipFile(wheel_path) as whl:
        metadata_file = [n for n in whl.namelist() if n.endswith("METADATA")][0]
        metadata = whl.read(metadata_file).decode("utf-8")

        assert "Name: test-meta" in metadata
        assert "Version: 1.0.0" in metadata
        assert "Requires-Dist: test-core[recommended]==1.0.0" in metadata
        assert "Requires-Python: >=3.9" in metadata


# =============================================================================
# Tests for static versioning
# =============================================================================


def test_build_static_version(integration_project_static):
    """Test building a metapackage with static version (no git needed)."""
    meta_dir = integration_project_static / "meta"

    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation"],
        cwd=meta_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"

    dist_dir = meta_dir / "dist"
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    wheel_path = wheels[0]
    # Static version is 2.5.0
    assert "test_meta-2.5.0" in wheel_path.name

    with zipfile.ZipFile(wheel_path) as whl:
        metadata_file = [n for n in whl.namelist() if n.endswith("METADATA")][0]
        metadata = whl.read(metadata_file).decode("utf-8")

        assert "Name: test-meta" in metadata
        assert "Version: 2.5.0" in metadata
        assert "Requires-Dist: test-core[recommended]==2.5.0" in metadata
        assert "Requires-Python: >=3.9" in metadata


def test_build_sdist_then_wheel_static(integration_project_static):
    """Test building wheel from sdist with static version."""
    meta_dir = integration_project_static / "meta"

    # Build sdist first
    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--sdist"],
        cwd=meta_dir,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"sdist build failed: {result.stderr}"

    dist_dir = meta_dir / "dist"
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(sdists) == 1

    # Extract sdist to a new location
    extract_dir = integration_project_static / "sdist_extract"
    with tarfile.open(sdists[0], "r:gz") as tar:
        if sys.version_info >= (3, 12):
            tar.extractall(extract_dir, filter="data")
        else:
            tar.extractall(extract_dir)

    extracted = list(extract_dir.iterdir())[0]

    # Build wheel from extracted sdist
    result = subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--wheel"],
        cwd=extracted,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Wheel build from sdist failed: {result.stderr}"

    wheels = list((extracted / "dist").glob("*.whl"))
    assert len(wheels) == 1

    with zipfile.ZipFile(wheels[0]) as whl:
        metadata_file = [n for n in whl.namelist() if n.endswith("METADATA")][0]
        metadata = whl.read(metadata_file).decode("utf-8")

        assert "Version: 2.5.0" in metadata
        assert "Requires-Dist: test-core[recommended]==2.5.0" in metadata
