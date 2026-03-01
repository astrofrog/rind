Usage Guide
===========

This guide walks through setting up a metapackage for an existing project.

Prerequisites
-------------

rind automatically detects and uses whatever versioning system your core package
uses. It supports:

- **Static versions** in ``pyproject.toml`` (no dependencies needed)
- **setuptools_scm** or **hatch-vcs** for git tag-based versioning
- **Any PEP 517 backend** as a fallback (calls the backend's metadata hook)

Both packages will get their version from the same source, ensuring that
``mypackage==1.2.3`` always installs ``mypackage-core==1.2.3``.

Repository Structure
--------------------

A typical setup has the metapackage configuration in a ``meta/`` subdirectory:

.. code-block:: text

   myproject/
   ├── pyproject.toml          # Core package (mypackage-core)
   │   mypackage/          # Actual code
   │   └── __init__.py
   └── meta/
       └── pyproject.toml      # Meta-package (mypackage)

or if you use the ``src`` layout for the main package:

.. code-block:: text

   myproject/
   ├── pyproject.toml          # Core package (mypackage-core)
   ├── src/
   │   └── mypackage/          # Actual code
   │       └── __init__.py
   └── meta/
       └── pyproject.toml      # Meta-package (mypackage)

Step 1: Configure the Core Package
----------------------------------

In your root ``pyproject.toml``, change the package name to include e.g. ``-core``
and configure setuptools_scm for versioning:

.. code-block:: toml

   [project]
   name = "mypackage-core"  # Was: "mypackage"
   dynamic = ["version"]
   description = "My package (core)"
   # ... rest of metadata

   [build-system]
   requires = ["setuptools>=61", "setuptools_scm>=8"]
   build-backend = "setuptools.build_meta"

   [tool.setuptools_scm]

Make sure dependencies are organized into the minimal required set plus optional extras:

.. code-block:: toml

   [project]
   dependencies = [
       "numpy>=1.20",
       "requests>=2.25",
   ]

   [project.optional-dependencies]
   # Features that require heavy dependencies
   ml = ["tensorflow>=2.0", "scikit-learn>=1.0"]
   viz = ["matplotlib>=3.5", "plotly>=5.0"]

   # Development extras
   test = ["pytest>=7.0", "pytest-cov"]
   docs = ["sphinx>=7.0", "sphinx-rtd-theme"]

.. important::

   The import name stays the same! Users still write ``import mypackage``,
   even though the package is now named ``mypackage-core`` on PyPI.

.. note::

   You can technically choose to not rename your core package and give your
   metapackage a different name (say ``mypackage-all``), although for
   established packages users will still need to discover the new metapackage
   name, which may not be much of an improvement compared to discovering extras.
   But it is your choice!

Step 2: Create the Meta-Package
-------------------------------

Create ``meta/pyproject.toml``:

.. code-block:: toml

   [build-system]
   requires = ["rind"]
   build-backend = "rind"

   [tool.rind]
   # Path to core package directory
   core-path = ".."

   # This is the metapackage name
   name = "mypackage"

   # Optional: override the description
   description = "My package (batteries included)"

   # Extras from core to make required in the metapackage
   include-extras = ["ml", "viz"]

   # Extras to pass through and expose on the metapackage (still optional)
   passthrough-extras = ["test", "docs"]

Step 3: Build Both Packages
---------------------------

.. code-block:: bash

   # Build the core package
   $ python -m build .

   # Build the metapackage
   $ python -m build meta/

This creates:

- ``dist/mypackage_core-1.0.0-py3-none-any.whl``
- ``meta/dist/mypackage-1.0.0-py3-none-any.whl``

Step 4: Release Together
------------------------

Both packages should be released simultaneously with the same version:

.. code-block:: bash

   # Tag the release
   $ git tag v1.0.0
   $ git push --tags

   # Build both
   $ python -m build .
   $ python -m build meta/

   # Upload both to PyPI
   $ twine upload dist/* meta/dist/*

User Experience
---------------

After release, users can choose their install:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Command
     - Result
   * - ``pip install mypackage-core``
     - Minimal: numpy, requests only
   * - ``pip install mypackage-core[ml]``
     - Core + TensorFlow, scikit-learn
   * - ``pip install mypackage``
     - Full: core + ml + viz
   * - ``pip install mypackage[test]``
     - Full + pytest

All options provide ``import mypackage`` because the actual code lives in
``mypackage-core`` but the package directory is named ``mypackage/``.
