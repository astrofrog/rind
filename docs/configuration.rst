Configuration Reference
=======================

All configuration for rind goes in the ``[tool.rind]``
table of your ``pyproject.toml``.

Required Options
----------------

name
~~~~

**Type:** string

The name of the meta-package. This is required and must be different from the
core package name.

.. code-block:: toml

   [tool.rind]
   name = "mypackage"

Inheritance Options
-------------------

inherit-metadata
~~~~~~~~~~~~~~~~

**Type:** string (path)

Path to a ``pyproject.toml`` file to inherit metadata from. Usually points to
the core package's configuration.

.. code-block:: toml

   [tool.rind]
   inherit-metadata = "../pyproject.toml"

When specified, the following fields are inherited (unless overridden):

- ``description``
- ``requires-python``
- ``license``
- ``authors``
- ``urls``
- ``classifiers``
- ``keywords``

.. note::

   The inherited metadata is cached in the sdist, so wheels can be built from
   the sdist without access to the parent ``pyproject.toml``.

Dependency Options
------------------

core-package
~~~~~~~~~~~~

**Type:** string

The name of the core package to depend on. Defaults to:

1. The ``name`` from inherited metadata (if ``inherit-metadata`` is set)
2. Otherwise, ``{name}-core``

.. code-block:: toml

   [tool.rind]
   core-package = "mypackage-core"

include-extras
~~~~~~~~~~~~~~

**Type:** list of strings

Extras from the core package to include as required dependencies in the
meta-package. These become part of the main ``Requires-Dist``.

.. code-block:: toml

   [tool.rind]
   # Users of the meta-package automatically get these extras
   include-extras = ["recommended", "performance"]

The resulting wheel will have:

.. code-block:: text

   Requires-Dist: mypackage-core[recommended,performance]==1.2.3

passthrough-extras
~~~~~~~~~~~~~~~~~~

**Type:** list of strings

Extras from the core package to re-expose in the meta-package. These remain
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

.. tip::

   Don't include extras in ``passthrough-extras`` that are already in
   ``include-extras``. Those are now required, not optional.

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

Version Options
---------------

version-root
~~~~~~~~~~~~

**Type:** string (path)

Root directory for setuptools_scm version detection. Defaults to ``".."``
(parent directory), which works when the meta-package is in a subdirectory.

.. code-block:: toml

   [tool.rind]
   version-root = ".."

If your meta-package is at the repository root (unusual), set this to ``"."``.

Complete Example
----------------

Here's a complete ``pyproject.toml`` for a meta-package:

.. code-block:: toml

   [build-system]
   requires = ["rind"]
   build-backend = "rind"

   [tool.rind]
   # Inherit from core package
   inherit-metadata = "../pyproject.toml"

   # Meta-package identity
   name = "mypackage"
   description = "My package with batteries included"

   # Core package (auto-detected from inheritance, but can override)
   # core-package = "mypackage-core"

   # Make these extras required
   include-extras = ["recommended", "performance"]

   # Keep these as optional extras
   passthrough-extras = ["test", "docs"]

   # Add extra dependencies not in core
   additional-dependencies = [
       "rich>=13.0",  # Nice CLI output
   ]
