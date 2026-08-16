"""Airfoil profile and wing loft.

The profile is checked against **published ordinate tables**, not against
itself: the NACA 4-digit family has been printed in the literature for eighty
years, so the coordinates have an external reference. The loft is checked
against the closed-form volume of a ruled loft between homothetic sections,
which is exact at zero twist.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from cad_context import airfoil, api, backends, exchange
from cad_context.generators.models import (
    AirfoilParams,
    WingParams,
    airfoil_area,
    airfoil_continuous_area,
    airfoil_outline,
    airfoil_payload,
    wing_bounds,
    wing_sections,
    wing_volume,
)

pytestmark = pytest.mark.usefixtures("cache")

# --- published references ----------------------------------------------------
# Abbott & von Doenhoff, *Theory of Wing Sections*, ordinates in per cent chord.
# The tables were computed with the original open trailing edge (-0.1015).

STATIONS = [0, 1.25, 2.5, 5.0, 7.5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 95, 100]

NACA_0012_HALF_THICKNESS = [
    0, 1.894, 2.615, 3.555, 4.200, 4.683, 5.345, 5.737, 5.941, 6.002,
    5.803, 5.294, 4.563, 3.664, 2.623, 1.448, 0.807, 0.126,
]  # fmt: skip

NACA_2412_UPPER = [
    0, 2.15, 2.99, 4.13, 4.96, 5.63, 6.61, 7.26, 7.67, 7.88,
    7.80, 7.24, 6.36, 5.18, 3.75, 2.08, 1.14, 0.13,
]  # fmt: skip

NACA_2412_LOWER = [
    0, -1.65, -2.27, -3.01, -3.46, -3.75, -4.10, -4.23, -4.22, -4.12,
    -3.80, -3.34, -2.76, -2.14, -1.50, -0.82, -0.45, -0.13,
]  # fmt: skip


def test_naca_0012_matches_the_published_thickness_table():
    """The symmetric case is a direct comparison — no interpolation involved."""
    stations = np.array(STATIONS) / 100.0
    ordinates = airfoil.thickness_ordinates(stations, 0.12, "open") * 100.0
    assert ordinates == pytest.approx(NACA_0012_HALF_THICKNESS, abs=0.001)


def test_naca_2412_matches_the_published_surface_table():
    """Cambered surfaces, resampled onto the table's stations.

    The exact construction lays each surface point normal to the camber line,
    so an upper-surface point is not at the station it came from; the published
    table lists both surfaces at the same stations, so the generated surfaces
    are interpolated back onto them. The leading edge is excluded: the table
    collapses both surfaces to a single 0 there, where the construction has no
    single station.
    """
    surface = airfoil.surfaces(
        thickness_ratio=0.12,
        max_camber=0.02,
        camber_position=0.4,
        points=2000,
        trailing_edge="open",
    )
    stations = np.array(STATIONS[1:]) / 100.0
    for name, published in (("upper", NACA_2412_UPPER), ("lower", NACA_2412_LOWER)):
        points = surface[name]
        order = np.argsort(points[:, 0])
        got = np.interp(stations, points[order, 0], points[order, 1]) * 100.0
        deviation = np.max(np.abs(got - np.array(published[1:])))
        assert deviation < 0.05, f"{name} surface deviates {deviation:.3f}% chord"


def test_camber_line_peaks_where_the_second_digit_says():
    ordinate, slope = airfoil.camber_ordinates(0.4, 0.02, 0.4)
    assert float(ordinate) == pytest.approx(0.02)
    assert float(slope) == pytest.approx(0.0, abs=1e-12)


def test_maximum_thickness_sits_at_thirty_per_cent_chord():
    for trailing_edge in airfoil.TRAILING_EDGES:
        assert airfoil.max_thickness_station(trailing_edge) == pytest.approx(
            0.30, abs=0.001
        )


# --- area: polygon, closed form, and the limit between them ------------------


def test_symmetric_area_matches_the_closed_form():
    """With no camber the ribbon integral collapses to the polynomial integral."""
    quadrature = airfoil.continuous_area_fraction(
        thickness_ratio=0.12, max_camber=0.0, trailing_edge="open"
    )
    closed_form = airfoil.thickness_area_fraction("open") * 0.12
    assert quadrature == pytest.approx(closed_form, rel=1e-12)


def test_polygon_area_converges_to_the_continuous_area():
    """Second-order convergence: tripling the stations cuts the error ~9x."""
    continuous = airfoil_continuous_area(AirfoilParams())
    errors = []
    for points in (30, 90, 270):
        polygon = airfoil_area(AirfoilParams(points=points))
        assert polygon < continuous  # an inscribed polygon never overshoots
        errors.append(abs(polygon - continuous) / continuous)
    assert errors[0] > errors[1] > errors[2]
    assert errors[2] < 1e-4
    assert errors[0] / errors[1] == pytest.approx(9.0, rel=0.25)


def test_area_scales_with_the_square_of_the_chord():
    small = airfoil_area(AirfoilParams(chord=60.0))
    large = airfoil_area(AirfoilParams(chord=120.0))
    assert large / small == pytest.approx(4.0, rel=1e-12)


# --- the outline a kernel receives -------------------------------------------


def test_outline_is_closed_counter_clockwise_and_free_of_duplicates():
    points = airfoil_outline(AirfoilParams())
    assert airfoil.signed_area(points) > 0.0
    steps = np.diff(np.vstack((points, points[:1])), axis=0)
    assert np.min(np.hypot(steps[:, 0], steps[:, 1])) > 0.0


@pytest.mark.parametrize(
    ("trailing_edge", "closes"), [("closed", True), ("open", False)]
)
def test_trailing_edge_choice_decides_whether_the_profile_closes(
    trailing_edge, closes
):
    surface = airfoil.surfaces(thickness_ratio=0.12, trailing_edge=trailing_edge)
    gap = float(np.hypot(*(surface["upper"][-1] - surface["lower"][-1])))
    assert (gap < 1e-12) is closes


def test_designation_names_the_family_member_and_admits_when_it_cannot():
    assert airfoil.designation(2.0, 40.0, 12.0) == "NACA 2412"
    assert airfoil.designation(0.0, 40.0, 12.0) == "NACA 0012"  # camber digit wins
    assert "(nearest)" in airfoil.designation(2.3, 41.0, 12.0)


# --- the 2D generator --------------------------------------------------------


@pytest.mark.skipif(not backends.available("shapely"), reason="vector2d extra missing")
def test_profile_generator_reports_a_valid_polygon_of_the_expected_area():
    metrics = api.metrics("airfoil", chord=150.0, thickness=15.0)
    expected = airfoil_area(AirfoilParams(chord=150.0, thickness=15.0))
    assert metrics["area"] == pytest.approx(expected, rel=1e-9)
    assert metrics["area"] == pytest.approx(metrics["area_continuous"], rel=1e-3)
    assert metrics["valid"] is True
    assert metrics["bounds"][2] == pytest.approx(150.0, abs=1e-9)


def test_cambered_nose_reaches_just_ahead_of_the_chord_line_origin():
    """The datum is the camber line's leading edge, not the outline's minimum.

    Surface points are offset normal to the camber line, and near the nose the
    thickness (∝ √x) outruns the station itself, so the upper surface dips a
    few ten-thousandths of a chord ahead of the origin. Real geometry, not a
    discretisation artefact — worth pinning so a future change to the datum is
    not mistaken for it.
    """
    points = airfoil_outline(AirfoilParams(chord=150.0, thickness=15.0))
    nose = float(points[:, 0].min())
    assert -0.001 * 150.0 < nose < 0.0
    assert airfoil_outline(AirfoilParams(max_camber=0.0))[:, 0].min() == pytest.approx(
        0.0, abs=1e-12
    )


@pytest.mark.skipif(not backends.available("shapely"), reason="vector2d extra missing")
def test_profile_exports_round_trip_including_the_coordinate_payload(cache):
    result = api.build("airfoil")
    exported = exchange.export(result, ["svg", "dxf", "json"])
    assert set(exported["files"]) == {"svg", "dxf", "json"}
    assert exported["skipped"] == {}

    measured = exported["measurements"]
    assert measured["svg"]["has_viewbox"] is True
    assert measured["dxf"]["units_name"] == "mm"
    assert measured["dxf"]["polylines"] == 1
    assert measured["json"]["curves"] == 3
    assert measured["json"]["units"] == "mm"

    payload = json.loads(exported["files"]["json"].read_text(encoding="utf-8"))
    outline = next(c for c in payload["curves"] if c["id"] == "outline")
    assert outline["closed"] is True
    assert len(outline["points"]) == len(airfoil_outline(AirfoilParams()))
    assert payload["designation"] == "NACA 2412"


def test_payload_marks_the_thickness_across_the_camber_line():
    """The marker spans the profile normal to the camber line, not vertically."""
    p = AirfoilParams()
    payload = airfoil_payload(p)
    marker = next(m for m in payload["markers"] if m["id"] == "max_thickness")
    (x_low, y_low), (x_high, y_high) = marker["segment"]
    station = airfoil.max_thickness_station(p.trailing_edge)
    peak = float(airfoil.thickness_ordinates(station, p.thickness / 100.0))
    # abs, not rel: payload coordinates are rounded to 1e-6 mm before writing.
    assert np.hypot(x_high - x_low, y_high - y_low) == pytest.approx(
        2.0 * peak * p.chord, abs=1e-5
    )
    # The polynomial peaks a whisker above the nominal thickness it is named for.
    assert 2.0 * peak == pytest.approx(p.thickness / 100.0, rel=1e-3)
    assert {
        m["id"] for m in airfoil_payload(AirfoilParams(max_camber=0.0))["markers"]
    } == {"max_thickness"}


# --- the 3D loft, on every installed kernel ----------------------------------


def test_wing_sections_are_planar_and_homothetic():
    p = WingParams(twist=0.0)
    root, tip = wing_sections(p)
    assert root[:, 1] == pytest.approx(0.0)
    assert tip[:, 1] == pytest.approx(p.span)
    # Both sections are the same profile: their chordwise extents are in the
    # taper ratio, and the tip is offset by the leading-edge sweep.
    root_chord = root[:, 0].max() - root[:, 0].min()
    tip_chord = tip[:, 0].max() - tip[:, 0].min()
    assert tip_chord / root_chord == pytest.approx(p.taper, rel=1e-9)


def test_untwisted_wing_volume_is_a_closed_form():
    p = WingParams(twist=0.0)
    sections_area = airfoil_area(p)
    assert wing_volume(p) == pytest.approx(
        sections_area * p.span * (1 + p.taper + p.taper**2) / 3.0
    )


def test_wing_loft_matches_the_analytic_volume_without_twist(wing_3d):
    """A ruled loft between homothetic sections *is* the closed-form solid."""
    metrics = api.metrics(wing_3d, twist=0.0)
    assert metrics["volume"] == pytest.approx(metrics["volume_analytic"], rel=1e-9)


def test_sweep_is_a_shear_and_does_not_change_the_volume(wing_3d):
    straight = api.metrics(wing_3d, twist=0.0, sweep=0.0)["volume"]
    swept = api.metrics(wing_3d, twist=0.0, sweep=30.0)["volume"]
    assert swept == pytest.approx(straight, rel=1e-9)


def test_wing_bounds_follow_span_and_sweep(wing_3d):
    p = WingParams(twist=0.0, sweep=0.0, span=400.0)
    metrics = api.metrics(wing_3d, **p.model_dump())
    expected = wing_bounds(p)
    assert metrics["bounds_min"] == pytest.approx(expected["min"], abs=1e-6)
    assert metrics["bounds_max"] == pytest.approx(expected["max"], abs=1e-6)


def test_twisted_wing_marks_the_analytic_reference_as_approximate(wing_3d):
    metrics = api.metrics(wing_3d, twist=-9.0)
    assert metrics["reference_exact"] is False
    assert metrics["volume"] == pytest.approx(metrics["volume_analytic"], rel=0.01)


def test_wing_exports_round_trip(cache, wing_3d):
    result = api.build(wing_3d, twist=0.0, points=60)
    exported = exchange.export(result, ["step", "stl", "glb"])
    assert exported["skipped"] == {}
    mesh = exported["measurements"]["mesh"]
    assert mesh["watertight"] is True
    assert mesh["volume"] == pytest.approx(result.metrics["volume_analytic"], rel=0.01)
    step = exchange.export3d.read_step_metrics(exported["files"]["step"])
    assert step["volume"] == pytest.approx(result.metrics["volume"], rel=1e-6)
