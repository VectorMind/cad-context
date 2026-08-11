"""3D wing section — ruled loft through airfoil sections, in build123d.

The twin of :mod:`cad_context.generators.wing_cadquery`: same section wires,
same ruled loft, a different kernel API driving it. Both are kept alive so the
web app can switch between them and the outputs can be compared directly
(OP-305) — the repository's rule is multiple real implementations, never an
approximation standing in for one.

The sections themselves are computed in
:func:`cad_context.generators.models.wing_sections`, so neither backend owns
any airfoil geometry.
"""

from __future__ import annotations

from ..types import BuildResult
from .models import (
    WingParams,
    airfoil_designation,
    wing_sections,
    wing_volume,
)

GENERATOR_ID = "wing-build123d"


def build(params: WingParams) -> BuildResult:
    from build123d import Face, Vector, Wire, loft

    p = params
    profiles = [
        Face(Wire.make_polygon([Vector(*point) for point in section], close=True))
        for section in wing_sections(p)
    ]
    # ruled: straight rules between corresponding vertices — a straight-taper
    # wing panel *is* a ruled surface, and it keeps the volume comparable with
    # the closed-form reference.
    part = loft(profiles, ruled=True)

    bbox = part.bounding_box()
    return BuildResult(
        generator=GENERATOR_ID,
        backend="build123d",
        kind="3d",
        params=p.model_dump(),
        native=part,
        metrics={
            "volume": part.volume,
            "volume_analytic": wing_volume(p),
            "area": part.area,
            "bounds_min": list(tuple(bbox.min)),
            "bounds_max": list(tuple(bbox.max)),
            "planform_area": p.span * p.chord * (1.0 + p.taper) / 2.0,
            "tip_chord": p.chord * p.taper,
            "designation": airfoil_designation(p),
            "units": "mm",
        },
    )
