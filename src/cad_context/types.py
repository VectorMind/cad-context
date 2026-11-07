"""Shared value types passed between generators, exporters and the CLI."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class Tessellation:
    """Generator-owned export quality; defaults preserve existing exporters."""

    linear_deflection: float = 0.01
    angular_deflection: float = 0.1
    stl_writer: Literal["occt", "mesher"] = "occt"

    def __post_init__(self) -> None:
        if self.stl_writer not in {"occt", "mesher"}:
            raise ValueError("stl_writer must be 'occt' or 'mesher'")
        for value in (self.linear_deflection, self.angular_deflection):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("tessellation deflections must be finite and positive")


@dataclass
class BuildResult:
    """The in-memory outcome of one generator run — never a file.

    ``native`` holds the backend's own object (a shapely geometry, a build123d
    ``Part``, or a solidpython2 object). Contracts live
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
    tessellation: Tessellation | None = None

    def summary(self) -> dict[str, Any]:
        """The picklable/JSON-able view — what agents usually want."""
        quality = asdict(self.tessellation) if self.tessellation else None
        if quality and quality["stl_writer"] == "occt":
            quality.pop("stl_writer")  # Preserve the existing default profile payload.
        return {
            "generator": self.generator,
            "backend": self.backend,
            "kind": self.kind,
            "params": self.params,
            "metrics": self.metrics,
            "tessellation": quality,
        }


class BackendUnavailable(RuntimeError):
    """A backend's Python dependency or external binary is missing."""
