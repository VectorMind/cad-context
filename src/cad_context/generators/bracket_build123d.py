"""3D reference part — flanged bracket, built with build123d (OCCT B-rep).

The parameter model and analytic reference are kernel-independent; this module
only drives the maintained build123d construction.
"""

from __future__ import annotations

from ..types import BuildResult
from .models import BracketParams, base_hole_centres, bracket_volume, web_hole_centres

GENERATOR_ID = "bracket-build123d"


def build(params: BracketParams) -> BuildResult:
    from build123d import Align, Box, Cylinder, Pos, Rot

    p = params
    radius = p.hole_diameter / 2.0
    overshoot = p.thickness * 3.0
    min_align = (Align.MIN, Align.MIN, Align.MIN)

    part = Box(p.width, p.depth, p.thickness, align=min_align) + Box(
        p.width, p.thickness, p.height, align=min_align
    )

    for x, y in base_hole_centres(p):
        part -= Pos(x, y, p.thickness / 2.0) * Cylinder(radius=radius, height=overshoot)
    for x, z in web_hole_centres(p):
        part -= (
            Pos(x, p.thickness / 2.0, z)
            * Rot(-90, 0, 0)
            * Cylinder(radius=radius, height=overshoot)
        )

    bbox = part.bounding_box()
    return BuildResult(
        generator=GENERATOR_ID,
        backend="build123d",
        kind="3d",
        params=p.model_dump(),
        native=part,
        metrics={
            "volume": part.volume,
            "volume_analytic": bracket_volume(p),
            "area": part.area,
            "bounds_min": list(tuple(bbox.min)),
            "bounds_max": list(tuple(bbox.max)),
            "units": "mm",
        },
    )
