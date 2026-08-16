"""Python surface for agents and scripts — returns data, never writes files.

Every function here is side-effect free: no ``.cache/`` writes, no geometry
files, no console output. Use it from a throwaway script or a REPL when you
want numbers or a live kernel object:

```python
from cad_context import api

api.metrics("bracket-build123d", width=90)     # -> dict of measurements
part = api.build("bracket-build123d").native   # -> live build123d object
```

Writing files is a separate, explicit decision: it happens through the
``cadctx`` CLI, or through :func:`cad_context.exchange.export` if a script
really needs artifacts. That split is what keeps ad-hoc agent scripts from
littering the workspace.
"""

from __future__ import annotations

from typing import Any

from . import backends as _backends
from . import generators as _generators
from . import workspace as _workspace
from .types import BuildResult


def generators() -> list[dict[str, Any]]:
    """Every registered generator with its backend, kind and formats."""
    return [
        {
            "id": spec.id,
            "title": spec.title,
            "kind": spec.kind,
            "backend": spec.backend,
            "family": spec.family,
            "formats": list(spec.formats),
            "available": _backends.available(spec.backend),
            "description": spec.description,
            "origin": spec.origin,
            "project": spec.project_name,
            "artifact_root": str(
                (spec.artifact_root or _workspace.cad_dir()).resolve()
            ),
            "exposure": spec.exposure,
        }
        for spec in _generators.specs()
    ]


def schema(generator_id: str) -> dict[str, Any]:
    """The parameter-schema payload for one generator."""
    return _generators.get(generator_id).schema()


def defaults(generator_id: str) -> dict[str, Any]:
    """Default parameter values for one generator."""
    return _generators.get(generator_id).parse().model_dump()


def build(generator_id: str, **params: Any) -> BuildResult:
    """Build a generator in memory. No files are written."""
    return _generators.get(generator_id).build(params)


def metrics(generator_id: str, **params: Any) -> dict[str, Any]:
    """Measured properties of a generated shape (volume, bounds, …)."""
    return build(generator_id, **params).metrics


def backend_status() -> list[dict[str, Any]]:
    """Which backends are importable, and where their binaries resolved."""
    return _backends.status()


def paths() -> dict[str, str]:
    """The workspace layout (``.cache/results``, ``.cache/cad``, …)."""
    return _workspace.layout()


__all__ = [
    "backend_status",
    "build",
    "defaults",
    "generators",
    "metrics",
    "paths",
    "schema",
]
