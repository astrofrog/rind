How It Works
============

This page explains the technical details of how rind works.

PEP 517 Build Backend
---------------------

rind is a `PEP 517 <https://peps.python.org/pep-0517/>`_ build
backend. When you run ``python -m build``, the build frontend:

1. Creates an isolated virtual environment
2. Installs the packages listed in ``build-system.requires``
3. Imports the module specified in ``build-system.build-backend``
4. Calls the appropriate hook functions (``build_wheel``, ``build_sdist``)

The backend implements these hooks to generate packages without any Python code.

Wheel Structure
---------------

A typical Python wheel contains:

.. code-block:: text

   mypackage-1.0.0-py3-none-any.whl
   ├── mypackage/
   │   ├── __init__.py
   │   └── module.py
   └── mypackage-1.0.0.dist-info/
       ├── METADATA
       ├── WHEEL
       └── RECORD

A rind wheel contains **only the metadata**:

.. code-block:: text

   mypackage-1.0.0-py3-none-any.whl
   └── mypackage-1.0.0.dist-info/
       ├── METADATA
       ├── WHEEL
       └── RECORD

This is perfectly valid according to the wheel specification. When pip installs
this wheel, it:

1. Records that ``mypackage==1.0.0`` is installed
2. Installs all packages listed in ``Requires-Dist``
3. Leaves no Python files (because there are none)

Version Pinning
---------------

Both the core package and meta-package use `setuptools_scm
<https://github.com/pypa/setuptools_scm>`_ to determine their version from git tags.

When you tag a release and build both packages:

.. code-block:: bash

   $ git tag v1.2.3
   $ python -m build .        # In repo root
   $ python -m build meta/    # In meta/ directory

Both builds call ``setuptools_scm.get_version()`` which reads the same git tag,
so both get version ``1.2.3``.

The meta-package's ``METADATA`` file contains:

.. code-block:: text

   Requires-Dist: mypackage-core==1.2.3

This ensures that ``pip install mypackage==1.2.3`` always installs
``mypackage-core==1.2.3``.

.. important::

   Version pinning only works correctly when both packages are built from the
   same git commit. Always build and release them together.

Metadata Inheritance
--------------------

When ``inherit-metadata`` is specified, the backend:

1. Reads the parent ``pyproject.toml``
2. Extracts the ``[project]`` table
3. Uses those values as defaults for the meta-package

The inheritance priority is:

1. ``[tool.rind]`` values (highest priority)
2. ``[project]`` values in the meta-package's own ``pyproject.toml``
3. Inherited values from parent ``pyproject.toml`` (lowest priority)

sdist and Inheritance
~~~~~~~~~~~~~~~~~~~~~

When building a wheel from an sdist, the parent ``pyproject.toml`` isn't
available (the sdist is extracted to a temporary directory).

To handle this, the backend caches the inherited metadata:

1. During ``build_sdist``, inherited metadata is saved to ``.rind_inherited.json``
2. This file is included in the sdist
3. During ``build_wheel``, the backend first checks for this cache file
4. If found, it uses the cached values instead of reading the parent file

This ensures wheels built from sdists have the same metadata as wheels built
directly from the repository.

Import Name vs Package Name
---------------------------

A key feature of this setup is that the **import name stays the same** while
the **package name changes**.

Consider this structure:

.. code-block:: text

   myproject/
   ├── pyproject.toml      # name = "mypackage-core"
   └── src/
       └── mypackage/      # Import name: mypackage
           └── __init__.py

The package installed via pip is ``mypackage-core``, but the directory
containing the code is ``mypackage/``, so users write:

.. code-block:: python

   import mypackage  # Works!

When ``mypackage`` (the meta-package) is installed, it pulls in ``mypackage-core``,
which provides the ``mypackage/`` directory. The meta-package itself provides
no Python files, so there's no conflict.

Comparison with Alternatives
----------------------------

**Why not use extras on a single package?**

You could use optional dependencies:

.. code-block:: toml

   [project]
   name = "mypackage"
   dependencies = ["numpy"]  # minimal

   [project.optional-dependencies]
   recommended = ["pandas", "matplotlib"]

Users install with ``pip install mypackage[recommended]``.

The meta-package approach is better when:

- You want the "batteries included" experience to be the default
- The package name without brackets should give the full experience
- You want clear separation between "essential" and "recommended"

**Why not two repositories?**

You could maintain separate repos for core and meta packages. The single-repo
approach is better because:

- Versions are automatically synchronized via git tags
- No coordination needed between repos for releases
- Single source of truth for metadata
- Easier CI/CD setup

Limitations
-----------

- **Both packages must be released together**: Since versions are synchronized
  via git tags, you can't release one without the other.

- **setuptools_scm is required**: The backend depends on setuptools_scm for
  version detection. If you need a different versioning approach, you'd need
  to modify the backend.

- **No code in meta-package**: The meta-package cannot contain any Python code.
  If you need wrapper code, it should go in the core package.
