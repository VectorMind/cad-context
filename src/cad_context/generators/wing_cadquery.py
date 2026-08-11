"""3D wing section — ruled loft through airfoil sections, in CadQuery.

The twin of :mod:`cad_context.generators.wing_build123d`. Same section wires
from :func:`cad_context.generators.models.wing_sections`, same ruled loft, so
the two backends are compared rather than ranked and the web app can switch
between them mid-session (OP-305).
"""

from __future__ import annotations

from ..types import BuildResult
from .models import (
    WingParams,
    airfoil_designation,
    wing_sections,
    wing_volume,
)

GENERATOR_ID = "wing-cadquery"


def build(params: WingParams) -> BuildResult:
    import cadquery as cq

    p = params
    wires = [
        cq.Wire.makePolygon([cq.Vector(*point) for point in section], close=True)
        for section in wing_sections(p)
    ]
    solid = cq.Solid.makeLoft(wires, ruled=True)
    part = cq.Workplane("XY").newObject([solid])

    bbox = solid.BoundingBox()
    return BuildResult(
        generator=GENERATOR_ID,
        backend="cadquery",
        kind="3d",
        params=p.model_dump(),
        native=part,
        metrics={
            "volume": solid.Volume(),
            "volume_analytic": wing_volume(p),
            "area": solid.Area(),
            "bounds_min": [bbox.xmin, bbox.ymin, bbox.zmin],
            "bounds_max": [bbox.xmax, bbox.ymax, bbox.zmax],
            "planform_area": p.span * p.chord * (1.0 + p.taper) / 2.0,
            "tip_chord": p.chord * p.taper,
            "designation": airfoil_designation(p),
            "units": "mm",
        },
    )
