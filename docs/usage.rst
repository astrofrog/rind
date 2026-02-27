Usage Guide
===========

This guide walks through setting up a meta-package for an existing project.

Repository Structure
--------------------

A typical setup has the meta-package configuration in a ``meta/`` subdirectory:

.. code-block:: text

   myproject/
   ├── pyproject.toml          # Core package (mypackage-core)
   ├── src/
   │   └── mypackage/          # Actual code
   │       └── __init__.py
   └── meta/
       └── pyproject.toml      # Meta-package (mypackage)

Step 1: Rename the Core Package
-------------------------------

In your root ``pyproject.toml``, change the package name to include ``-core``:

.. code-block:: toml

   [project]
   name = "mypackage-core"  # Was: "mypackage"
   version = "1.0.0"
   description = "My package (core)"
   # ... rest of metadata

Organize dependencies into the minimal required set plus optional extras:

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

Step 2: Create the Meta-Package
-------------------------------

Create ``meta/pyproject.toml``:

.. code-block:: toml

   [build-system]
   requires = ["rind"]
   build-backend = "rind"

   [tool.rind]
   # Inherit metadata from core package
   inherit-metadata = "../pyproject.toml"

   # This is the meta-package name
   name = "mypackage"

   # Optional: override the description
   description = "My package (batteries included)"

   # Extras from core to make required in the meta-package
   core-extras = ["ml", "viz"]

   # Extras to pass through (still optional)
   passthrough-extras = ["test", "docs"]

Step 3: Build Both Packages
---------------------------

.. code-block:: bash

   # Build the core package
   $ python -m build .

   # Build the meta-package
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

CI/CD Integration
-----------------

Here's an example GitHub Actions workflow for releasing both packages:

.. code-block:: yaml

   name: Release

   on:
     push:
       tags:
         - 'v*'

   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0  # Needed for setuptools_scm

         - uses: actions/setup-python@v5
           with:
             python-version: '3.12'

         - name: Install build tools
           run: pip install build twine

         - name: Build core package
           run: python -m build .

         - name: Build meta-package
           run: python -m build meta/

         - name: Upload to PyPI
           env:
             TWINE_USERNAME: __token__
             TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
           run: |
             twine upload dist/*
             twine upload meta/dist/*
