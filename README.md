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
core-extras = ["recommended", "optional"]

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
| `core-extras` | No | List of extras to include as required dependencies |
| `passthrough-extras` | No | List of extras to re-expose (with pinned versions) |
| `additional-dependencies` | No | Extra dependencies beyond the core package |
| `version-root` | No | Root for setuptools_scm (default: `".."`) |

## How Version Pinning Works

Both packages use [setuptools_scm](https://github.com/pypa/setuptools_scm) to get their version from git tags. When you tag a release:

```bash
git tag v1.2.3
python -m build .        # Creates mypackage_core-1.2.3-py3-none-any.whl
python -m build meta/    # Creates mypackage-1.2.3-py3-none-any.whl
                         # with Requires-Dist: mypackage-core==1.2.3
```

Since both builds use the same git state, versions always match.

## Example: reproject

The [reproject](https://github.com/astrofrog/reproject) package uses this backend:

**Root `pyproject.toml`** (reproject-core):
```toml
[project]
name = "reproject-core"
dependencies = ["numpy", "astrofrog", "scipy"]  # minimal

[project.optional-dependencies]
dask = ["dask", "zarr"]
hips = ["pillow", "pyavm"]
test = ["pytest"]
```

**`meta/pyproject.toml`** (reproject):
```toml
[build-system]
requires = ["rind"]
build-backend = "rind"

[tool.rind]
inherit-metadata = "../pyproject.toml"
name = "reproject"
core-extras = ["dask", "hips"]        # Now required
passthrough-extras = ["test"]          # Still optional
```

Result:
- `pip install reproject-core` → minimal dependencies
- `pip install reproject-core[dask]` → adds dask support
- `pip install reproject` → full experience (core + dask + hips)
- `pip install reproject[test]` → full experience + test dependencies

## License

BSD 3-Clause License. See [LICENSE](LICENSE) for details.
