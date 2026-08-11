"""cad-context — programmatic CAD workbench.

Two entry surfaces, same engine:

* ``cadctx`` CLI — the documented interface for humans and agents; it is the
  only surface that writes files.
* :mod:`cad_context.api` — pure Python functions returning data in memory;
  they never write files.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
