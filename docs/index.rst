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
  best experience
- **Advanced users** (library authors, Docker image builders, CI pipelines) want
  minimal installations to reduce dependency conflicts, image sizes, and install
  times

The recommended way to handle optional dependencies (including recommended but
not required dependencies) is to make use of extras, e.g.::

    pip install mypackage[recommended]

However, putting recommended dependencies behind extras places a burden on
typical users to discover and use this syntax, while making them required
penalizes advanced users who need lean installations.

Some projects may decide that using extras is not sufficient for their needs,
and instead distribute two packages: a core package with minimal dependencies
(e.g., ``mypackage-core``) and a metapackage (e.g., ``mypackage``) that depends
on the core and adds recommended dependencies.

The **rind** build backend is designed to significantly lower the maintenance
burden for projects that choose to provide two packages.

.. note::

    Splitting a package is not inherently better than using extras for
    recommended dependencies—it depends on your project's needs and user base.
    **rind** simply makes the split-package approach easier for projects that
    choose it.

Key Features
------------

- **Zero Python code**: The metapackage contains only metadata—no source files,
  just ``.dist-info/``.
- **Automatic versioning**: The metapackage version is derived from the core
  package at build time—no manual updates needed. Integrates with dynamic
  versioning tools like setuptools-scm and hatch-vcs.
- **Version pinning**: The metapackage pins to the exact core version, so
  ``mypackage==1.2.3`` always installs ``mypackage-core==1.2.3``.
- **Metadata inheritance**: Authors, license, URLs, and other metadata are
  automatically pulled from the core package.
- **Selective extras**: Control which extras become required dependencies, which
  pass through unchanged, and which are hidden.
- **Single repository**: Both packages live in the same repo—no need to manage
  separate repositories or release workflows.
- **Minimal changes**: The core package stays at the repository root; just add a
  small ``pyproject.toml`` in a subdirectory for the metapackage.
- **Standalone mode**: Can also create dependency bundles without a core package.

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
   core-path = ".."
   name = "mypackage"
   include-extras = ["recommended"]
   passthrough-extras = ["test", "docs"]

Then build both packages:

.. code-block:: bash

   $ python -m build .        # Build mypackage-core
   $ python -m build meta/    # Build mypackage (metapackage)

The result: ``pip install mypackage`` gives users the full experience with all
recommended dependencies, while ``pip install mypackage-core`` remains available
for those who need a minimal installation.

Why is this called rind?
------------------------

A pineapple has a tough **core**, sweet **flesh**, and a **rind** that wraps it
all up. Your package can be the same: a lean core, optional dependencies which
add tasty functionality (the flesh), and a metapackage to bundle them together
(the rind)—so users get the whole fruit with just ``pip install mypackage``!

Contents
--------

.. toctree::
   :maxdepth: 1

   installation
   usage
   configuration
   how-it-works
