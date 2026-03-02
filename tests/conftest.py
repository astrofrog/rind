"""Shared fixtures and constants for rind tests."""

import subprocess

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

# Core package with string license, classifiers, and keywords
CORE_PYPROJECT_FULL_METADATA = """\
[project]
name = "mypackage-core"
version = "3.0.0"
description = "My package core with full metadata"
requires-python = ">=3.9"
license = "MIT"
authors = [
    {name = "Test Author", email = "test@example.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: OSI Approved :: MIT License",
]
keywords = ["test", "package"]

[project.urls]
Homepage = "https://example.com"

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"
"""

META_PYPROJECT_FULL_METADATA = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
name = "mypackage"
"""

# Core package with keywords as comma-separated string
CORE_PYPROJECT_KEYWORDS_STRING = """\
[project]
name = "mypackage-core"
version = "3.0.0"
description = "My package core"
requires-python = ">=3.9"
keywords = "test, package, example"

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"
"""

META_PYPROJECT_KEYWORDS_STRING = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
name = "mypackage"
"""

# Core package with dynamic version via setuptools (not setuptools_scm)
# This exercises the _get_version_via_backend fallback
CORE_PYPROJECT_DYNAMIC_SETUPTOOLS = """\
[project]
name = "mypackage-core"
description = "My package core with dynamic version"
requires-python = ">=3.9"
dynamic = ["version"]

[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[tool.setuptools.dynamic]
version = {attr = "mypackage_core.__version__"}
"""

META_PYPROJECT_DYNAMIC_SETUPTOOLS = """\
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
core-path = "../core"
name = "mypackage"
"""


def _init_git_repo(path, tag):
    """Initialize a git repo with a tag."""
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "Initial"], cwd=path, check=True)
    subprocess.run(["git", "tag", tag], cwd=path, check=True)


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

    _init_git_repo(tmp_path, "v1.2.3")
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

    _init_git_repo(tmp_path, "v1.2.3")
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

    _init_git_repo(tmp_path, "v1.2.3")
    return tmp_path


@pytest.fixture
def temp_project_full_metadata(tmp_path):
    """Create a project with string license, classifiers, and keywords."""
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT_FULL_METADATA)

    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT_FULL_METADATA)

    return tmp_path


@pytest.fixture
def temp_project_keywords_string(tmp_path):
    """Create a project with keywords as comma-separated string."""
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT_KEYWORDS_STRING)

    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT_KEYWORDS_STRING)

    return tmp_path


@pytest.fixture
def temp_project_dynamic_setuptools(tmp_path):
    """Create a project with dynamic version via setuptools (not setuptools_scm)."""
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "pyproject.toml").write_text(CORE_PYPROJECT_DYNAMIC_SETUPTOOLS)

    # Create a Python package with __version__
    pkg_dir = core_dir / "mypackage_core"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").write_text('__version__ = "4.5.6"\n')

    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    (meta_dir / "pyproject.toml").write_text(META_PYPROJECT_DYNAMIC_SETUPTOOLS)

    return tmp_path
