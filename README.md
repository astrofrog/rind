# rind

A minimal [PEP 517](https://peps.python.org/pep-0517/) build backend for creating **meta-packages** — packages that contain no code, only dependencies.

## Why?

Sometimes you want to split a package into:

- **`mypackage-core`**: The actual code with minimal dependencies
- **`mypackage`**: A meta-package that installs `mypackage-core` plus recommended optional dependencies

This lets users choose between a lightweight install (`pip install mypackage-core`) or batteries-included (`pip install mypackage`), while both provide the same `import mypackage` experience.

## Features

- **Zero Python code in output**: Wheels contain only `.dist-info/` metadata
- **Automatic version pinning**: `mypackage==1.2.3` always installs `mypackage-core==1.2.3`
- **Metadata inheritance**: Reuse authors, license, URLs from the core package's `pyproject.toml`
- **Selective extras**: Choose which extras to pass through vs. make required
- **Single repository**: Both packages live in the same repo, tagged together

## Quick Start

Create a `meta/` directory in your repository with this `pyproject.toml`:

```toml
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
# Inherit metadata from the core package
inherit-metadata = "../pyproject.toml"

# The meta-package name (the core package keeps the original name)
name = "mypackage"

# Extras from core to include as default dependencies
include-extras = ["recommended", "optional"]

# Extras to pass through (not included by default, but available)
passthrough-extras = ["test", "docs"]
```

Build both packages:

```bash
python -m build .        # Build mypackage-core
python -m build meta/    # Build mypackage (meta-package)
```

## Configuration Reference

All options go in `[tool.rind]`:

| Option | Required | Description |
|--------|----------|-------------|
| `name` | Yes | Name of the meta-package |
| `inherit-metadata` | No | Path to parent `pyproject.toml` to inherit from |
| `description` | No | Override inherited description |
| `core-package` | No | Core package name (default: inherited name or `{name}-core`) |
| `include-extras` | No | List of extras to include as required dependencies |
| `passthrough-extras` | No | List of extras to re-expose (with pinned versions) |
| `additional-dependencies` | No | Extra dependencies beyond the core package |
| `version-root` | No | Root for setuptools_scm (default: `".."`) |

## How Version Pinning Works

rind uses [setuptools_scm](https://github.com/pypa/setuptools_scm) to get the version from git tags. **Your core package must also use setuptools_scm** for version pinning to work correctly. When you tag a release:

```bash
git tag v1.2.3
python -m build .        # Creates mypackage_core-1.2.3-py3-none-any.whl
python -m build meta/    # Creates mypackage-1.2.3-py3-none-any.whl
                         # with Requires-Dist: mypackage-core==1.2.3
```

Since both builds use the same git state, versions always match.

## Example

**Root `pyproject.toml`** (mypackage-core):
```toml
[project]
name = "mypackage-core"
dependencies = ["numpy"]

[project.optional-dependencies]
recommended = ["scipy", "matplotlib"]
test = ["pytest"]
docs = ["sphinx"]
```

**`meta/pyproject.toml`** (mypackage):
```toml
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
inherit-metadata = "../pyproject.toml"
name = "mypackage"
include-extras = ["recommended"]
passthrough-extras = ["test", "docs"]
```

Result:
- `pip install mypackage-core` → just numpy
- `pip install mypackage-core[recommended]` → numpy + scipy + matplotlib
- `pip install mypackage` → numpy + scipy + matplotlib (recommended included by default)
- `pip install mypackage[test]` → above + pytest

## License

BSD 3-Clause License. See [LICENSE](LICENSE) for details.
