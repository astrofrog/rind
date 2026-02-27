# rind

> **Warning**
> This package is experimental and under active development. The API may change without notice.

A minimal [PEP 517](https://peps.python.org/pep-0517/) build backend for creating **meta-packages** — packages that extend a core package by installing additional dependencies.

## Why use rind?

Package maintainers often face a tension between two types of users:

- **Typical users** want recommended dependencies installed by default for the best experience, without needing to know about extras syntax like `pip install mypackage[recommended]`
- **Advanced users** (library authors, Docker image builders, CI pipelines) want minimal installations to reduce dependency conflicts, image sizes, and install times

Putting recommended dependencies behind extras places a burden on typical users to discover and use special syntax. But making them required penalizes advanced users who need lean installations.

**rind solves this** by letting you publish two packages from a single repository:

- **`mypackage-core`**: Minimal dependencies for advanced users
- **`mypackage`**: Batteries-included for typical users (installs `mypackage-core` plus recommended extras)

Both provide the same `import mypackage` experience.

## How to use rind

See the `documentation <https://rind.readthedocs.io>_` for information on how to use this package.

## License

BSD 3-Clause License. See [LICENSE](LICENSE) for details.
