"""Parameter models and kernel-independent analytic geometry.

This module must stay import-cheap: no CAD kernel imports. Backends import it,
never the other way round. The analytic formulas here are the ground truth the
per-backend exports are checked against (cross-backend agreement proof).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from .. import airfoil
from ..params import ShapeParams, choice, integer, number


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


class AirfoilParams(ShapeParams):
    """A NACA 4-digit profile, as three continuous knobs plus a chord.

    The four digits are the parameterisation: maximum camber, its chordwise
    position, and the thickness — held as percentages of chord so a slider
    moves smoothly between named members of the family instead of snapping to
    the digit grid.

    Datum: the camber line's leading edge at the origin, chord along +X, chord
    line on Y=0. That is the datum the parameters are defined against, so it is
    the datum the exports carry (`specifications/exchange-formats/spec.md`).
    The *outline* reaches a few ten-thousandths of a chord ahead of it, because
    surface points are offset normal to the camber line. Units are millimetres.
    """

    chord: float = number(
        120.0,
        minimum=20.0,
        maximum=600.0,
        description="Chord length, leading edge to trailing edge",
    )
    max_camber: float = number(
        2.0,
        minimum=0.0,
        maximum=9.0,
        step=0.1,
        unit="% chord",
        description="Maximum camber — the first NACA digit",
    )
    camber_position: float = number(
        40.0,
        minimum=10.0,
        maximum=90.0,
        step=1.0,
        unit="% chord",
        description="Chordwise position of maximum camber — the second NACA digit",
    )
    thickness: float = number(
        12.0,
        minimum=4.0,
        maximum=30.0,
        step=0.1,
        unit="% chord",
        description="Maximum thickness — the last two NACA digits",
    )
    points: int = integer(
        90,
        minimum=30,
        maximum=300,
        step=10,
        unit="",
        description="Cosine-spaced coordinate stations per surface",
    )
    trailing_edge: str = choice(
        "closed",
        options=list(airfoil.TRAILING_EDGES),
        description="Closed trailing edge, or the original open-TE coefficient",
    )


class WingParams(AirfoilParams):
    """A straight-taper wing section lofted from the profile above.

    Root section at Y=0 on the airfoil datum, tip at Y=span; every section is
    the same profile scaled by the local chord, rotated about its own
    quarter-chord point by the local twist, and offset by the leading-edge
    sweep. Thickness runs along +Z, so the part is Z-up like every other 3D
    part in the repository.
    """

    span: float = number(
        300.0, minimum=40.0, maximum=2000.0, description="Root-to-tip span"
    )
    taper: float = number(
        0.6,
        minimum=0.2,
        maximum=1.0,
        step=0.05,
        unit="",
        description="Tip chord divided by root chord",
    )
    twist: float = number(
        -3.0,
        minimum=-15.0,
        maximum=15.0,
        step=0.5,
        unit="deg",
        description="Tip incidence relative to the root (negative is washout)",
    )
    sweep: float = number(
        15.0,
        minimum=-15.0,
        maximum=45.0,
        step=0.5,
        unit="deg",
        description="Leading-edge sweep angle",
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


# --- airfoil and wing geometry, expressed once ------------------------------


def airfoil_kwargs(p: AirfoilParams) -> dict[str, Any]:
    """Percent-of-chord parameters as the chord fractions the math works in."""
    return {
        "thickness_ratio": p.thickness / 100.0,
        "max_camber": p.max_camber / 100.0,
        "camber_position": p.camber_position / 100.0,
        "points": p.points,
        "trailing_edge": p.trailing_edge,
    }


def airfoil_outline(p: AirfoilParams) -> np.ndarray:
    """The closed profile polygon in millimetres, counter-clockwise."""
    return airfoil.outline(**airfoil_kwargs(p)) * p.chord


def airfoil_area(p: AirfoilParams) -> float:
    """Exact area of the generated profile — the 2D reference value.

    Deliberately the shoelace area of the very polygon the exporters and the
    loft sections are built from: it is a kernel-free reference that also keeps
    the discretisation visible instead of hiding it inside the reference.
    :func:`airfoil_continuous_area` is the discretisation-free counterpart the
    polygon converges to.
    """
    return airfoil.signed_area(airfoil_outline(p))


def airfoil_continuous_area(p: AirfoilParams) -> float:
    """Area of the continuous profile — the limit of the polygon area."""
    kwargs = airfoil_kwargs(p)
    kwargs.pop("points")
    return airfoil.continuous_area_fraction(**kwargs) * p.chord**2


def airfoil_designation(p: AirfoilParams) -> str:
    return airfoil.designation(p.max_camber, p.camber_position, p.thickness)


def airfoil_payload(p: AirfoilParams) -> dict[str, Any]:
    """The plot payload written as the generator's JSON artifact.

    Plain coordinates and overlay markers: the curves a profile plot draws, and
    the two annotations that make a parameter change legible (where the maximum
    thickness sits, where the maximum camber sits). A consumer renders it
    without knowing anything about airfoils — and never recomputes geometry of
    its own.
    """
    surface = airfoil.surfaces(**airfoil_kwargs(p))
    outline_mm = airfoil_outline(p)
    kwargs = airfoil_kwargs(p)

    station = airfoil.max_thickness_station(p.trailing_edge)
    half = float(
        airfoil.thickness_ordinates(
            station, kwargs["thickness_ratio"], p.trailing_edge
        )
    )
    camber_y, slope = airfoil.camber_ordinates(
        station, kwargs["max_camber"], kwargs["camber_position"]
    )
    angle = math.atan(float(slope))
    upper_point = (
        (station - half * math.sin(angle)) * p.chord,
        (float(camber_y) + half * math.cos(angle)) * p.chord,
    )
    lower_point = (
        (station + half * math.sin(angle)) * p.chord,
        (float(camber_y) - half * math.cos(angle)) * p.chord,
    )

    def points(array: np.ndarray) -> list[list[float]]:
        return [[round(float(x), 6), round(float(y), 6)] for x, y in array]

    minx, miny = outline_mm.min(axis=0)
    maxx, maxy = outline_mm.max(axis=0)
    markers = [
        {
            "id": "max_thickness",
            "label": f"t {p.thickness:.1f}% c at {station * 100:.1f}% c",
            "segment": [
                [round(lower_point[0], 6), round(lower_point[1], 6)],
                [round(upper_point[0], 6), round(upper_point[1], 6)],
            ],
        }
    ]
    if p.max_camber > 0.0:
        markers.append(
            {
                "id": "max_camber",
                "label": (
                    f"camber {p.max_camber:.1f}% c at {p.camber_position:.0f}% c"
                ),
                "point": [
                    round(p.camber_position / 100.0 * p.chord, 6),
                    round(p.max_camber / 100.0 * p.chord, 6),
                ],
            }
        )

    return {
        "kind": "profile",
        "generator": "airfoil",
        "units": "mm",
        "designation": airfoil_designation(p),
        "chord": p.chord,
        "bounds": [
            round(float(minx), 6),
            round(float(miny), 6),
            round(float(maxx), 6),
            round(float(maxy), 6),
        ],
        "curves": [
            {
                "id": "outline",
                "role": "surface",
                "closed": True,
                "points": points(outline_mm),
            },
            {
                "id": "camber",
                "role": "guide",
                "closed": False,
                "points": points(surface["camber"] * p.chord),
            },
            {
                "id": "chord_line",
                "role": "guide",
                "closed": False,
                "points": [[0.0, 0.0], [round(p.chord, 6), 0.0]],
            },
        ],
        "markers": markers,
    }


#: Twist rotates each section about its own quarter-chord point — the
#: aerodynamic convention, and the point sweep is measured from.
TWIST_AXIS_FRACTION = 0.25

#: Spanwise stations of the lofted sections. Taper, twist and sweep are all
#: linear in span, so root and tip define the ruled solid exactly.
SECTION_FRACTIONS = (0.0, 1.0)


def wing_sections(p: WingParams) -> list[np.ndarray]:
    """The section polygons of the wing, as (N, 3) millimetre point arrays.

    Computed here rather than in the kernel module so the design geometry and
    its analytic reference remain independent of build123d.
    """
    base = airfoil.outline(**airfoil_kwargs(p))
    sweep_gradient = math.tan(math.radians(p.sweep))
    sections: list[np.ndarray] = []
    for fraction in SECTION_FRACTIONS:
        chord = p.chord * (1.0 + (p.taper - 1.0) * fraction)
        axis = TWIST_AXIS_FRACTION * chord
        angle = math.radians(p.twist * fraction)
        cos, sin = math.cos(angle), math.sin(angle)
        along = base[:, 0] * chord - axis
        across = base[:, 1] * chord
        x = axis + along * cos + across * sin + p.span * fraction * sweep_gradient
        z = -along * sin + across * cos
        y = np.full_like(x, p.span * fraction)
        sections.append(np.column_stack((x, y, z)))
    return sections


def wing_volume(p: WingParams) -> float:
    """Volume of the ruled loft between root and tip — the reference value.

    Every intermediate section of a ruled loft between two homothetic polygons
    is that polygon scaled, so the spanwise area distribution is quadratic and
    integrates in closed form to ``A·s·(1 + k + k²)/3``. Sweep is a shear and
    leaves it untouched. Twist does not: it rotates the sections, and a ruled
    loft between rotated sections loses a term of second order in the angle, so
    this value is exact at ``twist == 0`` and a reference elsewhere — which is
    why the cross-backend check quotes the twist it ran at.
    """
    return airfoil_area(p) * p.span * (1.0 + p.taper + p.taper**2) / 3.0


def wing_bounds(p: WingParams) -> dict[str, tuple[float, float, float]]:
    """Axis-aligned bounding box of the lofted wing in its own frame."""
    stacked = np.vstack(wing_sections(p))
    low, high = stacked.min(axis=0), stacked.max(axis=0)
    return {"min": tuple(float(v) for v in low), "max": tuple(float(v) for v in high)}
