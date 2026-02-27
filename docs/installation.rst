Installation
============

rind is a build-time dependency, so you typically don't install
it directly. Instead, you declare it in your metapackage's ``pyproject.toml``:

.. code-block:: toml

   [build-system]
   requires = ["rind"]
   build-backend = "rind"

When you run ``python -m build``, the build frontend (pip, build, etc.) will
automatically install rind in an isolated environment.

Development Installation
------------------------

If you want to work on rind itself:

.. code-block:: bash

   $ git clone https://github.com/astrofrog/rind
   $ cd rind
   $ pip install -e ".[test,docs]"

Requirements
------------

- Python 3.9 or later
- setuptools_scm (for version detection from git tags)

The backend automatically declares ``setuptools_scm`` as a build dependency,
so you don't need to add it to your ``build-system.requires``.
