# rind

> **Warning**
> This package is experimental and under active development. The API may change without notice.

A minimal [PEP 517](https://peps.python.org/pep-0517/) build backend for creating **meta-packages** — packages that extend a core package by installing additional dependencies.

## Why use rind?

Package maintainers often face a tension between two types of users:

- **Typical users** want recommended dependencies installed by default for the best experience, without needing to know about extras syntax like `pip install mypackage[recommended]`
- **Advanced users** (library authors, Docker image builders, CI pipelines) want minimal installations to reduce dependency conflicts, image sizes, and install times

Putting recommended dependencies behind extras places a burden on typical users to discover and use special syntax. But making them required penalizes advanced users who need lean installations.

One solution is to distribute two packages: a core package with minimal dependencies (e.g., `mypackage-core`) and a meta-package (e.g., `mypackage`) that depends on the core and adds recommended dependencies. However, this approach comes with maintenance challenges: versions must be carefully pinned, and metadata must be kept in sync.

**rind eliminates this burden** by letting you publish both packages from a single repository with automatic version pinning and metadata inheritance:

- **`mypackage-core`**: Minimal dependencies for advanced users
- **`mypackage`**: Batteries-included for typical users

Both provide the same `import mypackage` experience.

## Documentation

See the [documentation](https://rind.readthedocs.io) for information on how to use this package.

## License

BSD 3-Clause License. See [LICENSE](LICENSE) for details.
