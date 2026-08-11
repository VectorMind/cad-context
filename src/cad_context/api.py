"""Python surface for agents and scripts — returns data, never writes files.

Every function here is side-effect free: no ``.cache/`` writes, no geometry
files, no console output. Use it from a throwaway script or a REPL when you
want numbers or a live kernel object:

```python
from cad_context import api

api.metrics("bracket-cadquery", width=90)      # -> dict of measurements
part = api.build("bracket-build123d").native   # -> live build123d object
api.compare(width=90)                          # -> cross-backend volumes
api.compare(family="wing", twist=0)            # -> the same, for the wing loft
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
        }
        for spec in _generators.SPECS
    ]


def schema(generator_id: str) -> dict[str, Any]:
    """The parameter-schema payload for one generator."""
    return _generators.get(generator_id).schema()


def defaults(generator_id: str) -> dict[str, Any]:
    """Default parameter values for one generator."""
    from .params import defaults as _defaults

    return _defaults(_generators.get(generator_id).params_model)


def build(generator_id: str, **params: Any) -> BuildResult:
    """Build a generator in memory. No files are written."""
    return _generators.get(generator_id).build(params)


def metrics(generator_id: str, **params: Any) -> dict[str, Any]:
    """Measured properties of a generated shape (volume, bounds, …)."""
    return build(generator_id, **params).metrics


def compare(*, family: str = "bracket", **params: Any) -> dict[str, Any]:
    """Build one family's part on every available backend and compare volumes.

    Only generators of the same family are comparable: they build the same part
    from the same parameters, so one analytic volume is the reference for all of
    them. Uses each kernel's own volume where it has one; OpenSCAD has no
    in-process kernel, so it reports analytic only unless the CLI renders and
    measures its STL.
    """
    rows: dict[str, Any] = {}
    reference: float | None = None
    for spec in _generators.family(family, kind="3d"):
        if not _backends.available(spec.backend):
            continue
        result = build(spec.id, **params)
        volume = result.metrics.get("volume")
        reference = reference or result.metrics.get("volume_analytic")
        rows[spec.id] = {
            "backend": spec.backend,
            "volume": volume,
            "volume_analytic": result.metrics.get("volume_analytic"),
        }
    measured = [r["volume"] for r in rows.values() if r["volume"] is not None]
    deviation = None
    if measured and reference:
        deviation = max(abs(v - reference) / reference for v in measured)
    return {
        "family": family,
        "params": params,
        "reference_volume": reference,
        "backends": rows,
        "max_deviation": deviation,
    }


def backend_status() -> list[dict[str, Any]]:
    """Which backends are importable, and where their binaries resolved."""
    return _backends.status()


def paths() -> dict[str, str]:
    """The workspace layout (``.cache/results``, ``.cache/cad``, …)."""
    return _workspace.layout()


__all__ = [
    "backend_status",
    "build",
    "compare",
    "defaults",
    "generators",
    "metrics",
    "paths",
    "schema",
]
