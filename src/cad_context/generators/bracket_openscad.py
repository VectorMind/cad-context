"""3D reference part — flanged bracket, built with solidpython2 (OpenSCAD CSG).

This backend degrades gracefully: the Python side always produces the OpenSCAD
source, and the mesh is only rendered when an ``openscad`` binary is resolvable
(``cadctx fetch openscad``, then ``.tools/`` or ``PATH``).
"""

from __future__ import annotations

from ..types import BuildResult
from .models import BracketParams, base_hole_centres, bracket_volume, web_hole_centres

GENERATOR_ID = "bracket-openscad"

#: Facet count for cylinders; high enough that faceting error on the holes
#: stays far below the 1% cross-backend volume tolerance.
FACETS = 96


def build(params: BracketParams) -> BuildResult:
    from solid2 import cube, cylinder

    p = params
    radius = p.hole_diameter / 2.0
    overshoot = p.thickness * 3.0

    model = cube([p.width, p.depth, p.thickness]) + cube(
        [p.width, p.thickness, p.height]
    )
    for x, y in base_hole_centres(p):
        model -= cylinder(r=radius, h=overshoot, _fn=FACETS).translate(
            [x, y, -p.thickness]
        )
    for x, z in web_hole_centres(p):
        model -= (
            cylinder(r=radius, h=overshoot, _fn=FACETS)
            .rotate([-90, 0, 0])
            .translate([x, -p.thickness, z])
        )

    return BuildResult(
        generator=GENERATOR_ID,
        backend="openscad",
        kind="3d",
        params=p.model_dump(),
        native=model,
        metrics={
            # OpenSCAD has no in-process kernel: the analytic value is the
            # reference, and the measured value appears once trimesh loads the
            # rendered STL (see cad_context.exchange.export3d).
            "volume_analytic": bracket_volume(p),
            "facets": FACETS,
            "units": "mm",
        },
    )
