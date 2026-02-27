rind
===================

.. warning::

   This package is experimental and under active development.
   The API may change without notice.

A minimal [PEP 517](https://peps.python.org/pep-0517/) build backend for
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

One possible solution is to distribute two packages - a core package with only
minimal dependencies (e.g. ``mypackage-core``) and a metapackage (e.g.
``mypackage``) which depends on ``mypackage-core`` and also installs additional
dependencies. However, this can mean additional maintenance burden, as it
requires careful pinning of versions in the metapackage to make sure that e.g.
``mypackage==1.2.3`` will install ``mypackage-core==1.2.3``. In addition, metadata
such as authors, extras, and so on need to be kept in sync between the two packages.

**rind aims to make this approach as easy as possible** by letting you easily publish two packages
from a single repository:

- **mypackage-core**: Minimal dependencies for advanced users
- **mypackage**: Batteries-included for typical users (installs ``mypackage-core``
  plus recommended extras)

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

Let's say you have a package ``mypackage`` which you want to split between
``mypackage-core`` and ``mypackage``. You can keep the core package as the main
package in the reposiotory and rename it to ``mypackage-core``.

In a subdirectory of your repository (e.g. ``meta/``), create a new ``pyproject.toml``:

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
