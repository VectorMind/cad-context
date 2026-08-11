"""2D airfoil profile — NACA 4-digit, built with shapely.

Pure geometry: returns a shapely polygon, the plot payload, and metrics; writes
nothing. The coordinates come from :mod:`cad_context.airfoil`, so the SVG, the
DXF, the JSON plot payload and the 3D loft sections are all the same points.
"""

from __future__ import annotations

from ..types import BuildResult
from .models import (
    AirfoilParams,
    airfoil_area,
    airfoil_continuous_area,
    airfoil_designation,
    airfoil_outline,
    airfoil_payload,
)

GENERATOR_ID = "airfoil"


def build(params: AirfoilParams) -> BuildResult:
    from shapely.geometry import Polygon

    p = params
    points = airfoil_outline(p)
    shape = Polygon(points)
    minx, miny, maxx, maxy = shape.bounds
    return BuildResult(
        generator=GENERATOR_ID,
        backend="shapely",
        kind="2d",
        params=p.model_dump(),
        native=shape,
        payload=airfoil_payload(p),
        metrics={
            "area": shape.area,
            "area_analytic": airfoil_area(p),
            "area_continuous": airfoil_continuous_area(p),
            "perimeter": shape.length,
            "bounds": [minx, miny, maxx, maxy],
            "vertices": len(points),
            "valid": shape.is_valid,
            "designation": airfoil_designation(p),
            "units": "mm",
        },
    )
