rind
====

.. warning::

   This package is experimental and under active development.
   The API may change without notice.

A minimal `PEP 517 <https://peps.python.org/pep-0517/>`_ build backend for
creating **meta-packages** — packages that extend a core package by installing
additional dependencies.

.. note::

   A meta-package is a package that exists solely to aggregate dependencies.
   When installed, it pulls in other packages but provides no code of its own.

Why use rind?
-------------

Package maintainers often face a tension between two types of users:

- **Typical users** want recommended dependencies installed by default for the
  best experience, without needing to know about extras syntax like
  ``pip install mypackage[recommended]``
- **Advanced users** (library authors, Docker image builders, CI pipelines) want
  minimal installations to reduce dependency conflicts, image sizes, and install
  times

Putting recommended dependencies behind extras places a burden on typical users
to discover and use special syntax. But making them required penalizes advanced
users who need lean installations.

One solution is to distribute two packages: a core package with minimal
dependencies (e.g., ``mypackage-core``) and a meta-package (e.g., ``mypackage``)
that depends on the core and adds recommended dependencies. However, this
approach comes with maintenance challenges:

- Versions must be carefully pinned so that ``mypackage==1.2.3`` installs
  ``mypackage-core==1.2.3``
- Metadata (authors, license, URLs, extras) must be kept in sync between packages

**rind eliminates this burden** by letting you publish both packages from a
single repository with automatic version pinning and metadata inheritance:

- **mypackage-core**: Minimal dependencies for advanced users
- **mypackage**: Batteries-included for typical users

Both provide the same ``import mypackage`` experience, since the code lives in
``mypackage-core`` but the import name remains ``mypackage``.

Key Features
------------

- **Zero Python code**: Output wheels contain only ``.dist-info/`` metadata
- **Automatic version pinning**: ``mypackage==1.2.3`` always installs
  ``mypackage-core==1.2.3``
- **Metadata inheritance**: Reuse authors, license, URLs from the core package
- **Selective extras**: Choose which extras to make required vs. pass through
- **Single repository**: Both packages live in the same repo, share the same tags

Quick Example
-------------

Suppose you have a package ``mypackage`` that you want to split into
``mypackage-core`` and ``mypackage``. Keep the core package as the main
package in your repository and rename it to ``mypackage-core``.

In a subdirectory (e.g., ``meta/``), create a ``pyproject.toml`` for the
meta-package:

.. code-block:: toml

   [build-system]
   requires = ["rind"]
   build-backend = "rind"

   [tool.rind]
   inherit-metadata = "../pyproject.toml"
   name = "mypackage"
   include-extras = ["recommended"]
   passthrough-extras = ["test", "docs"]

Then build both packages:

.. code-block:: bash

   $ python -m build .        # Build mypackage-core
   $ python -m build meta/    # Build mypackage (meta-package)

Contents
--------

.. toctree::
   :maxdepth: 2

   installation
   usage
   configuration
   how-it-works

Indices and tables
------------------

* :ref:`genindex`
* :ref:`search`
