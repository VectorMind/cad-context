"""2D reference part — slotted plate, built with shapely.

Pure geometry: returns a shapely polygon plus metrics, writes nothing.
"""

from __future__ import annotations

from typing import Any

from ..types import BuildResult
from .models import PlateParams, plate_area

GENERATOR_ID = "plate2d"


def build(params: PlateParams) -> BuildResult:
    from shapely.geometry import Point, box
    from shapely.ops import unary_union

    p = params
    outer = box(0.0, 0.0, p.width, p.height)
    if p.corner_radius > 0.0:
        # Erode-then-dilate rounds the corners without changing the envelope.
        outer = outer.buffer(-p.corner_radius, join_style="round", quad_segs=32).buffer(
            p.corner_radius, join_style="round", quad_segs=32
        )

    cuts: list[Any] = []
    spacing = p.width / (p.slot_count + 1)
    cap = p.slot_width / 2.0
    straight = max(p.slot_length - p.slot_width, 0.0) / 2.0
    cy = p.height / 2.0
    for i in range(1, p.slot_count + 1):
        cx = spacing * i
        stem = box(cx, cy - straight, cx, cy + straight)
        cuts.append(stem.buffer(cap, quad_segs=32))

    inset = max(p.corner_radius, p.hole_diameter) + p.hole_diameter / 2.0
    for hx, hy in (
        (inset, inset),
        (p.width - inset, inset),
        (inset, p.height - inset),
        (p.width - inset, p.height - inset),
    ):
        cuts.append(Point(hx, hy).buffer(p.hole_diameter / 2.0, quad_segs=32))

    shape = outer.difference(unary_union(cuts))
    minx, miny, maxx, maxy = shape.bounds
    return BuildResult(
        generator=GENERATOR_ID,
        backend="shapely",
        kind="2d",
        params=p.model_dump(),
        native=shape,
        metrics={
            "area": shape.area,
            "area_analytic": plate_area(p),
            "perimeter": shape.length,
            "bounds": [minx, miny, maxx, maxy],
            "rings": 1 + len(shape.interiors),
            "valid": shape.is_valid,
            "units": "mm",
        },
    )
