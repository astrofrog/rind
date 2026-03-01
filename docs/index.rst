rind
====

.. warning::

   This package is experimental and under active development.
   The API may change without notice.

A minimal `PEP 517 <https://peps.python.org/pep-0517/>`_ build backend to make
it easy to create a **metapackage** that extends
a core package by installing additional dependencies.

.. note::

   A metapackage is a package that exists solely to aggregate dependencies.
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
dependencies (e.g., ``mypackage-core``) and a metapackage (e.g., ``mypackage``)
that depends on the core and adds recommended dependencies. However, this
approach comes with maintenance challenges:

- Versions must be carefully pinned so that ``mypackage==1.2.3`` installs
  ``mypackage-core==1.2.3``
- Metadata (versions, authors, license, URLs, etc.) must be kept in sync between packages
- Extras might need to be re-exposed in the metapackage if you want to keep them optional

**rind eliminates this burden** by letting you define a metapackage in the same
repository as your core package, and will handle automatic version pinning,
metadata inheritance, and passing

It does not require you to switch fully to a monorepo-style layout - you can
keep your main package as the primary package at the root of the repository, and
you can include the minimal metadata for the metapackage in a subdirectory.

Key Features
------------

- **Zero Python code**: Output wheels for the metapackage contain only ``.dist-info/`` metadata
- **Automatic version pinning**: ``mypackage==1.2.3`` always installs
  ``mypackage-core==1.2.3``
- **Metadata inheritance**: Reuse authors, license, URLs from the core package
- **Selective extras**: Choose which extras to make required vs. pass through
- **Single repository**: Both packages live in the same repo, share the same tags

What's with the name?
---------------------

Some fruits such as pineapples have a tough **core**, sweet flesh, and a
**rind** that wraps it all up. Your package can be the same: a lean core users
can install with e.g. ``pip install mypackage-core``, optional dependencies
which add tasty functionality (the flesh), and a metapackage to bundle them
together (the rind) — so users get the whole fruit with e.g. ``pip install
mypackage``. Enough with the terrible metaphor? Let's dive in!

Quick Example
-------------

Suppose you have a package ``mypackage`` that you want to split into
``mypackage-core`` and ``mypackage``. Keep the core package as the main
package in your repository and rename it to ``mypackage-core``.

In a subdirectory (e.g., ``meta/``), create a ``pyproject.toml`` for the
metapackage:

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
   $ python -m build meta/    # Build mypackage (metapackage)

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
