"""Parameter models and analytic geometry shared by every backend.

This module must stay import-cheap: no CAD kernel imports. Backends import it,
never the other way round. The analytic formulas here are the ground truth the
per-backend exports are checked against (cross-backend agreement proof).
"""

from __future__ import annotations

import math

from ..params import ShapeParams, integer, number


class BracketParams(ShapeParams):
    """The reference 3D part: an L-shaped flanged bracket with four holes.

    Built identically by every 3D backend, so their exported volumes must
    agree. Coordinate frame: base plate on the XY plane at Z=0, web plate
    rising in +Z from the Y=0 edge. Units are millimetres.
    """

    width: float = number(
        80.0, minimum=20.0, maximum=300.0, description="Overall X width of both plates"
    )
    depth: float = number(
        60.0, minimum=20.0, maximum=300.0, description="Y depth of the base plate"
    )
    height: float = number(
        50.0, minimum=20.0, maximum=300.0, description="Z height of the web plate"
    )
    thickness: float = number(
        6.0, minimum=2.0, maximum=30.0, step=0.5, description="Plate thickness"
    )
    hole_diameter: float = number(
        8.0,
        minimum=2.0,
        maximum=40.0,
        step=0.5,
        description="Diameter of the four holes",
    )


class PlateParams(ShapeParams):
    """The reference 2D part: a rounded plate with slots and corner holes."""

    width: float = number(
        120.0, minimum=40.0, maximum=400.0, description="Plate width (X)"
    )
    height: float = number(
        80.0, minimum=40.0, maximum=400.0, description="Plate height (Y)"
    )
    corner_radius: float = number(
        8.0, minimum=0.0, maximum=40.0, step=0.5, description="Corner rounding radius"
    )
    slot_count: int = integer(
        3, minimum=1, maximum=9, unit="", description="Number of vertical slots"
    )
    slot_width: float = number(
        10.0, minimum=2.0, maximum=40.0, step=0.5, description="Slot width"
    )
    slot_length: float = number(
        40.0, minimum=10.0, maximum=300.0, description="Slot length including caps"
    )
    hole_diameter: float = number(
        6.0, minimum=1.0, maximum=30.0, step=0.5, description="Corner hole diameter"
    )


# --- bracket geometry, expressed once ---------------------------------------

BASE_HOLE_Y_FRACTION = 0.65
WEB_HOLE_Z_FRACTION = 0.65
HOLE_X_FRACTIONS = (0.25, 0.75)


def base_hole_centres(p: BracketParams) -> list[tuple[float, float]]:
    """(x, y) centres of the two holes drilled through the base plate (Z axis)."""
    y = p.depth * BASE_HOLE_Y_FRACTION
    return [(p.width * fx, y) for fx in HOLE_X_FRACTIONS]


def web_hole_centres(p: BracketParams) -> list[tuple[float, float]]:
    """(x, z) centres of the two holes drilled through the web plate (Y axis)."""
    z = p.height * WEB_HOLE_Z_FRACTION
    return [(p.width * fx, z) for fx in HOLE_X_FRACTIONS]


def bracket_volume(p: BracketParams) -> float:
    """Exact volume of the bracket — the cross-backend reference value."""
    base = p.width * p.depth * p.thickness
    web = p.width * p.thickness * p.height
    overlap = p.width * p.thickness * p.thickness
    holes = 4.0 * math.pi * (p.hole_diameter / 2.0) ** 2 * p.thickness
    return base + web - overlap - holes


def bracket_bounds(p: BracketParams) -> dict[str, tuple[float, float, float]]:
    """Axis-aligned bounding box of the bracket in its own frame."""
    return {"min": (0.0, 0.0, 0.0), "max": (p.width, p.depth, p.height)}


def plate_area(p: PlateParams) -> float:
    """Exact area of the 2D plate (rounded rectangle minus slots and holes)."""
    rect = p.width * p.height
    corners = (4.0 - math.pi) * p.corner_radius**2
    slot = (p.slot_length - p.slot_width) * p.slot_width + math.pi * (
        p.slot_width / 2.0
    ) ** 2
    holes = 4.0 * math.pi * (p.hole_diameter / 2.0) ** 2
    return rect - corners - p.slot_count * slot - holes
