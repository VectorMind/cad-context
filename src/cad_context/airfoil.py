"""NACA 4-digit airfoil geometry — textbook math, numpy only.

No CAD kernel and no airfoil library: the family is a handful of polynomials,
and keeping them here means the coordinates can be checked against published
ordinate tables directly, and reused by the 2D exporter, the 3D loft sections
and the plot payload without any of them re-deriving geometry.

Everything works in **chord fractions** (x/c, y/c) and takes plain floats and
numpy arrays. Millimetres appear only when a caller multiplies by a chord;
parameter objects live in :mod:`cad_context.generators.models`, which wraps
these functions.

The profile is built on the aerodynamic datum: the camber line's leading edge
at the origin, chord along +x, chord line on y = 0.
"""

from __future__ import annotations

import math

import numpy as np

#: Thickness distribution of the family:
#: ``y_t/c = 5 t (a0 √x + a1 x + a2 x² + a3 x³ + a4 x⁴)``.
SQRT_COEFFICIENT = 0.2969
POLY_COEFFICIENTS = (-0.1260, -0.3516, 0.2843)

#: The last coefficient decides the trailing edge. ``-0.1015`` is the original
#: NACA value and leaves a finite TE thickness (0.21% of the thickness ratio);
#: ``-0.1036`` closes the trailing edge exactly, which is what a solid modeller
#: wants. Published ordinate tables use the open value.
TRAILING_EDGE_COEFFICIENT = {"open": -0.1015, "closed": -0.1036}
TRAILING_EDGES = tuple(TRAILING_EDGE_COEFFICIENT)


def _te_coefficient(trailing_edge: str) -> float:
    try:
        return TRAILING_EDGE_COEFFICIENT[trailing_edge]
    except KeyError:
        known = ", ".join(TRAILING_EDGES)
        raise ValueError(
            f"unknown trailing_edge {trailing_edge!r}; known: {known}"
        ) from None


def cosine_stations(count: int) -> np.ndarray:
    """``count`` chordwise stations from 0 to 1, clustered at both edges.

    Cosine spacing puts the points where the curvature is: uniform spacing
    would round off the leading edge and waste points on the flat mid-chord.
    """
    if count < 3:
        raise ValueError(f"need at least 3 stations, got {count}")
    return 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, count)))


def thickness_ordinates(
    x: np.ndarray | float, thickness_ratio: float, trailing_edge: str = "closed"
) -> np.ndarray:
    """Half-thickness ``y_t/c`` at chordwise stations ``x``."""
    x = np.asarray(x, dtype=float)
    a1, a2, a3 = POLY_COEFFICIENTS
    a4 = _te_coefficient(trailing_edge)
    return (
        5.0
        * thickness_ratio
        * (
            SQRT_COEFFICIENT * np.sqrt(x)
            + a1 * x
            + a2 * x**2
            + a3 * x**3
            + a4 * x**4
        )
    )


def camber_ordinates(
    x: np.ndarray | float, max_camber: float, camber_position: float
) -> tuple[np.ndarray, np.ndarray]:
    """Mean camber line ``y_c/c`` and its slope ``dy_c/dx``.

    Two parabolas meeting at the position of maximum camber, as defined by the
    first two NACA digits. A profile with zero camber (or a degenerate camber
    position) is flat, and its slope is zero everywhere.
    """
    x = np.asarray(x, dtype=float)
    m, p = float(max_camber), float(camber_position)
    if m == 0.0 or not 0.0 < p < 1.0:
        flat = np.zeros_like(x)
        return flat, flat.copy()
    fore = x < p
    ordinate = np.where(
        fore,
        m / p**2 * (2.0 * p * x - x**2),
        m / (1.0 - p) ** 2 * ((1.0 - 2.0 * p) + 2.0 * p * x - x**2),
    )
    slope = np.where(
        fore,
        2.0 * m / p**2 * (p - x),
        2.0 * m / (1.0 - p) ** 2 * (p - x),
    )
    return ordinate, slope


def surfaces(
    *,
    thickness_ratio: float,
    max_camber: float = 0.0,
    camber_position: float = 0.4,
    points: int = 90,
    trailing_edge: str = "closed",
) -> dict[str, np.ndarray]:
    """Upper, lower and camber coordinates in chord fractions, leading edge first.

    Surface points are laid **normal to the camber line** — the standard
    construction — so the upper and lower surfaces do not share their x
    stations once the profile is cambered.
    """
    stations = cosine_stations(points)
    half = thickness_ordinates(stations, thickness_ratio, trailing_edge)
    camber, slope = camber_ordinates(stations, max_camber, camber_position)
    angle = np.arctan(slope)
    sin, cos = np.sin(angle), np.cos(angle)
    return {
        "stations": stations,
        "upper": np.column_stack((stations - half * sin, camber + half * cos)),
        "lower": np.column_stack((stations + half * sin, camber - half * cos)),
        "camber": np.column_stack((stations, camber)),
        "half_thickness": half,
    }


def outline(
    *,
    thickness_ratio: float,
    max_camber: float = 0.0,
    camber_position: float = 0.4,
    points: int = 90,
    trailing_edge: str = "closed",
) -> np.ndarray:
    """The closed profile polygon in chord fractions, counter-clockwise.

    Ordered trailing edge → upper surface → leading edge → lower surface, with
    no repeated vertex: the leading edge is shared by both surfaces, and so is
    the trailing edge when it is closed. A duplicated vertex would become a
    zero-length edge in a kernel wire.
    """
    surface = surfaces(
        thickness_ratio=thickness_ratio,
        max_camber=max_camber,
        camber_position=camber_position,
        points=points,
        trailing_edge=trailing_edge,
    )
    upper, lower = surface["upper"], surface["lower"]
    closed_te = bool(np.allclose(upper[-1], lower[-1]))
    tail = lower[1:-1] if closed_te else lower[1:]
    polygon = np.vstack((upper[::-1], tail))
    if signed_area(polygon) < 0.0:  # keep the winding a promise, not a hope
        polygon = polygon[::-1]
    return polygon


def signed_area(points: np.ndarray) -> float:
    """Shoelace area of a closed polygon given without a repeated last vertex."""
    x, y = points[:, 0], points[:, 1]
    return 0.5 * float(
        np.dot(x, np.roll(y, -1)) - np.dot(np.roll(x, -1), y)
    )


def perimeter(points: np.ndarray) -> float:
    """Closed-polygon perimeter."""
    closed = np.vstack((points, points[:1]))
    steps = np.diff(closed, axis=0)
    return float(np.sum(np.hypot(steps[:, 0], steps[:, 1])))


def max_thickness_station(trailing_edge: str = "closed") -> float:
    """Chordwise position of maximum thickness (≈0.30 for the whole family).

    Independent of the thickness ratio: it only scales the distribution. Found
    as the root of ``dy_t/du`` in ``u = √x``, where the distribution is an
    ordinary polynomial.
    """
    a1, a2, a3 = POLY_COEFFICIENTS
    a4 = _te_coefficient(trailing_edge)
    derivative = np.polynomial.Polynomial(
        [SQRT_COEFFICIENT, 2.0 * a1, 0.0, 4.0 * a2, 0.0, 6.0 * a3, 0.0, 8.0 * a4]
    )
    candidates = [
        root.real
        for root in derivative.roots()
        if abs(root.imag) < 1e-9 and 0.0 < root.real <= 1.0
    ]
    if not candidates:  # pragma: no cover - the family always has one
        raise RuntimeError("thickness distribution has no interior maximum")
    stations = np.array(candidates) ** 2
    return float(stations[np.argmax(thickness_ordinates(stations, 1.0, trailing_edge))])


def thickness_area_fraction(trailing_edge: str = "closed") -> float:
    """``A / (t c²)`` for an uncambered profile — closed form, exact.

    The symmetric profile encloses ``∫ 2 y_t dx``, and the distribution
    integrates term by term.
    """
    a1, a2, a3 = POLY_COEFFICIENTS
    a4 = _te_coefficient(trailing_edge)
    integral = (
        SQRT_COEFFICIENT * (2.0 / 3.0) + a1 / 2.0 + a2 / 3.0 + a3 / 4.0 + a4 / 5.0
    )
    return 10.0 * integral


def continuous_area_fraction(
    *,
    thickness_ratio: float,
    max_camber: float = 0.0,
    camber_position: float = 0.4,
    trailing_edge: str = "closed",
    nodes: int = 48,
) -> float:
    """``A / c²`` of the *continuous* profile — the discretisation-free reference.

    The cambered profile is the ribbon of half-width ``y_t`` laid normal to the
    camber line, so its area is exactly ``∫ 2 y_t √(1 + y_c'²) dx``: the
    curvature corrections of the two surfaces cancel over the symmetric width.
    Substituting ``x = ξ²`` removes the √x branch point at the leading edge and
    leaves a polynomial integrand on each side of the camber break, so
    Gauss–Legendre quadrature reaches machine precision rather than merely
    converging.
    """
    m, p = float(max_camber), float(camber_position)
    abscissae, weights = np.polynomial.legendre.leggauss(nodes)
    breaks = [0.0, 1.0] if (m == 0.0 or not 0.0 < p < 1.0) else [0.0, math.sqrt(p), 1.0]
    total = 0.0
    for low, high in zip(breaks[:-1], breaks[1:], strict=False):
        middle, halfspan = (high + low) / 2.0, (high - low) / 2.0
        xi = middle + halfspan * abscissae
        x = xi**2
        half = thickness_ordinates(x, thickness_ratio, trailing_edge)
        _, slope = camber_ordinates(x, m, p)
        integrand = 2.0 * half * np.sqrt(1.0 + slope**2) * 2.0 * xi  # dx = 2ξ dξ
        total += halfspan * float(np.dot(weights, integrand))
    return total


def designation(
    max_camber_percent: float, camber_position_percent: float, thickness_percent: float
) -> str:
    """The four-digit name of a profile, e.g. ``NACA 2412``.

    Sliders move continuously between the named members of the family, so a
    profile that does not land on the digit grid is reported as the nearest
    one rather than pretending to be it.
    """
    camber_digit = round(max_camber_percent)
    position_digit = 0 if camber_digit == 0 else round(camber_position_percent / 10.0)
    thickness_digits = round(thickness_percent)
    exact = (
        abs(max_camber_percent - camber_digit) < 1e-9
        and (
            camber_digit == 0
            or abs(camber_position_percent / 10.0 - position_digit) < 1e-9
        )
        and abs(thickness_percent - thickness_digits) < 1e-9
    )
    name = f"NACA {camber_digit}{position_digit}{thickness_digits:02d}"
    return name if exact else f"{name} (nearest)"
