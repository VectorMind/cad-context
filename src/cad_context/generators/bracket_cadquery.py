"""3D reference part — flanged bracket, built with CadQuery (OCCT B-rep).

Holes are cut as explicit cylinders rather than through workplane selectors so
that the construction is literally the same as the build123d and OpenSCAD
versions — that is what makes the cross-backend volume comparison meaningful.
"""

from __future__ import annotations

from ..types import BuildResult
from .models import BracketParams, base_hole_centres, bracket_volume, web_hole_centres

GENERATOR_ID = "bracket-cadquery"


def build(params: BracketParams) -> BuildResult:
    import cadquery as cq
    from cadquery import Vector

    p = params
    radius = p.hole_diameter / 2.0
    overshoot = p.thickness * 3.0

    base = cq.Solid.makeBox(p.width, p.depth, p.thickness, Vector(0, 0, 0))
    web = cq.Solid.makeBox(p.width, p.thickness, p.height, Vector(0, 0, 0))
    solid = base.fuse(web).clean()

    cutters = [
        cq.Solid.makeCylinder(
            radius, overshoot, Vector(x, y, -p.thickness), Vector(0, 0, 1)
        )
        for x, y in base_hole_centres(p)
    ] + [
        cq.Solid.makeCylinder(
            radius, overshoot, Vector(x, -p.thickness, z), Vector(0, 1, 0)
        )
        for x, z in web_hole_centres(p)
    ]
    solid = solid.cut(*cutters).clean()

    workplane = cq.Workplane(obj=solid)
    bbox = solid.BoundingBox()
    return BuildResult(
        generator=GENERATOR_ID,
        backend="cadquery",
        kind="3d",
        params=p.model_dump(),
        native=workplane,
        metrics={
            "volume": solid.Volume(),
            "volume_analytic": bracket_volume(p),
            "area": solid.Area(),
            "bounds_min": [bbox.xmin, bbox.ymin, bbox.zmin],
            "bounds_max": [bbox.xmax, bbox.ymax, bbox.zmax],
            "units": "mm",
        },
    )
