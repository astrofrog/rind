Configuration Reference
=======================

All configuration for rind goes in the ``[tool.rind]``
table of your ``pyproject.toml``.

Core Package Options
--------------------

These options are used when wrapping a core package. For standalone metapackages
(dependency bundles without a core package), see :ref:`standalone-mode` below.

core-path
~~~~~~~~~

**Type:** string (path)

Path to the directory containing your core package's ``pyproject.toml``.
This tells rind where to find the core package.

.. code-block:: toml

   [tool.rind]
   core-path = ".."

The core package's ``pyproject.toml`` is used to:

- Determine the version (using whatever versioning system the core uses)
- Get the core package name (from ``[project] name``)
- Inherit metadata fields like authors, license, URLs (if ``inherit-metadata`` is true)

.. note::

   If ``core-path`` is not specified, rind operates in **standalone mode** where
   all metadata must be provided directly in ``[project]``.

name
~~~~

**Type:** string

The name of the metapackage. Required when using ``core-path``. Must be different
from the core package name.

.. code-block:: toml

   [tool.rind]
   name = "mypackage"

In standalone mode, specify the name in ``[project]`` instead.

Inheritance Options
-------------------

inherit-metadata
~~~~~~~~~~~~~~~~

**Type:** boolean (default: ``true``)

Whether to inherit metadata fields from the core package. When true, the
following fields are inherited (unless overridden):

- ``description``
- ``requires-python``
- ``license``
- ``authors``
- ``urls``
- ``classifiers``
- ``keywords``

.. code-block:: toml

   [tool.rind]
   # Inherit metadata (default)
   inherit-metadata = true

   # Or disable inheritance
   inherit-metadata = false

.. note::

   The inherited metadata is resolved and stored in the sdist's ``pyproject.toml``,
   so wheels can be built from the sdist without access to the core package.

Dependency Options
------------------

include-extras
~~~~~~~~~~~~~~

**Type:** list of strings

Extras from the core package to include as required dependencies in the
metapackage. These become part of the main ``Requires-Dist``.

.. code-block:: toml

   [tool.rind]
   # Users of the metapackage automatically get these extras
   include-extras = ["recommended", "performance"]

The resulting wheel will have:

.. code-block:: text

   Requires-Dist: mypackage-core[recommended,performance]==1.2.3

passthrough-extras
~~~~~~~~~~~~~~~~~~

**Type:** list of strings

Extras from the core package to re-expose in the metapackage. These remain
optional but are pinned to the same version.

.. code-block:: toml

   [tool.rind]
   passthrough-extras = ["test", "docs", "dev"]

The resulting wheel will have:

.. code-block:: text

   Provides-Extra: test
   Requires-Dist: mypackage-core[test]==1.2.3; extra == 'test'
   Provides-Extra: docs
   Requires-Dist: mypackage-core[docs]==1.2.3; extra == 'docs'

Note that you can use ``["*"]`` to pass through all extras from the core package:

.. code-block:: toml

   [tool.rind]
   passthrough-extras = ["*"]

This is particularly useful for existing packages transitioning to use rind.
By passing through all extras, the metapackage preserves full backward
compatibility - any code that previously depended on
``mypackage[someextra]`` will continue to work unchanged with the new
metapackage structure.

.. note::

   It's fine if an extra appears in both ``include-extras`` and
   ``passthrough-extras`` (either explicitly or via ``["*"]``). When a user
   installs the passthrough extra, it will be a no-op since that extra's
   dependencies are already installed as part of the main package. This
   means you don't need to carefully exclude ``include-extras`` from your
   passthrough list.

additional-dependencies
~~~~~~~~~~~~~~~~~~~~~~~

**Type:** list of strings

Additional dependencies beyond the core package. Use standard PEP 508 syntax.

.. code-block:: toml

   [tool.rind]
   additional-dependencies = [
       "some-other-package>=2.0",
       "another-package[extra]>=1.5",
   ]

Metadata Overrides
------------------

Any field that can be inherited can also be overridden by specifying it
directly in ``[tool.rind]``:

description
~~~~~~~~~~~

**Type:** string

Override the inherited description.

.. code-block:: toml

   [tool.rind]
   description = "My package with all recommended dependencies"

You can also override these in a ``[project]`` table, though ``[tool.rind]``
takes precedence:

.. code-block:: toml

   [project]
   # These are checked after [tool.rind] but before inherited values
   requires-python = ">=3.10"

   [tool.rind]
   # This takes highest precedence
   description = "Override description"

Complete Example
----------------

Here's a complete ``pyproject.toml`` for a metapackage:

.. code-block:: toml

   [build-system]
   requires = ["rind"]
   build-backend = "rind"

   [tool.rind]
   # Path to core package directory (required)
   core-path = ".."

   # Meta-package identity
   name = "mypackage"
   description = "My package with batteries included"

   # Make these extras required
   include-extras = ["recommended", "performance"]

   # Pass through all extras for backward compatibility
   passthrough-extras = ["*"]

   # Add extra dependencies not in core
   additional-dependencies = [
       "rich>=13.0",  # Nice CLI output
   ]

.. _standalone-mode:

Standalone Mode
---------------

rind can also create metapackages without a core package. This is useful for
creating curated dependency bundles (e.g., "my-data-science-stack").

In standalone mode, omit ``core-path`` and specify all metadata directly in
``[project]``:

.. code-block:: toml

   [build-system]
   requires = ["rind"]
   build-backend = "rind"

   [project]
   name = "my-data-science-stack"
   version = "1.0.0"
   description = "A curated collection of data science packages"
   requires-python = ">=3.9"
   dependencies = [
       "pandas>=2.0",
       "numpy>=1.24",
       "matplotlib>=3.7",
   ]

   [project.optional-dependencies]
   ml = ["scikit-learn>=1.3", "tensorflow>=2.13"]

Key differences from core-package mode:

- Version must be static (specified directly in ``[project]``)
- No metadata inheritance (everything in ``[project]``)
- No ``include-extras`` or ``passthrough-extras`` (define extras directly)
- No automatic version pinning
