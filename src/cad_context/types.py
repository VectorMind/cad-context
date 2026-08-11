"""Shared value types passed between generators, exporters and the CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BuildResult:
    """The in-memory outcome of one generator run — never a file.

    ``native`` holds the backend's own object (a shapely geometry, a CadQuery
    ``Workplane``, a build123d ``Part``, a solidpython2 object). Contracts live
    at the export boundary, so nothing outside the owning backend module is
    allowed to interpret it.

    ``payload`` is the opposite: backend-neutral plain data (curve coordinates,
    overlay markers) that a generator publishes for consumers to draw. It is
    written verbatim by the ``json`` exchange format, and anything may read it.
    """

    generator: str
    backend: str
    kind: str  # "2d" | "3d"
    params: dict[str, Any]
    native: Any = None
    metrics: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] | None = None

    def summary(self) -> dict[str, Any]:
        """The picklable/JSON-able view — what agents usually want."""
        return {
            "generator": self.generator,
            "backend": self.backend,
            "kind": self.kind,
            "params": self.params,
            "metrics": self.metrics,
        }


class BackendUnavailable(RuntimeError):
    """A backend's Python dependency or external binary is missing."""
