"""The Python surface: data in memory, and no files on disk."""

from __future__ import annotations

import math

import pytest

from cad_context import api, backends
from cad_context.generators.models import (
    BracketParams,
    PlateParams,
    bracket_volume,
    plate_area,
)

pytestmark = pytest.mark.usefixtures("cache")


def _cache_files(root):
    return sorted(p for p in root.rglob("*") if p.is_file()) if root.exists() else []


def test_api_build_writes_nothing(cache, generator_3d):
    before = _cache_files(cache)
    result = api.build(generator_3d, width=90.0)
    assert result.native is not None
    assert result.params["width"] == 90.0
    assert _cache_files(cache) == before


def test_kernel_volume_matches_the_analytic_reference(generator_3d):
    metrics = api.metrics(generator_3d, width=90.0)
    expected = bracket_volume(BracketParams(width=90.0))
    assert metrics["volume_analytic"] == pytest.approx(expected)
    if "volume" in metrics:  # OpenSCAD has no in-process kernel
        assert metrics["volume"] == pytest.approx(expected, rel=1e-6)


@pytest.mark.skipif(not backends.available("shapely"), reason="vector2d extra missing")
def test_plate_area_matches_the_analytic_reference():
    metrics = api.metrics("plate2d", width=160.0, slot_count=5)
    expected = plate_area(PlateParams(width=160.0, slot_count=5))
    assert metrics["area"] == pytest.approx(expected, rel=1e-3)
    assert metrics["valid"] is True
    assert metrics["rings"] == 1 + 5 + 4  # outline + slots + corner holes


@pytest.mark.skipif(not backends.available("shapely"), reason="vector2d extra missing")
def test_plate_bounds_follow_the_parameters():
    metrics = api.metrics("plate2d", width=200.0, height=100.0)
    assert metrics["bounds"] == pytest.approx([0.0, 0.0, 200.0, 100.0], abs=1e-6)


def test_compare_agrees_across_available_kernels():
    payload = api.compare(width=90.0)
    assert payload["reference_volume"] == pytest.approx(
        bracket_volume(BracketParams(width=90.0))
    )
    if payload["max_deviation"] is not None:
        assert payload["max_deviation"] < 0.01


def test_generators_and_paths_are_pure_data():
    listed = api.generators()
    assert {g["id"] for g in listed} >= {"plate2d", "bracket-cadquery"}
    assert set(api.paths()) >= {"cache", "results", "reports", "cad"}
    assert all(isinstance(row["available"], bool) for row in api.backend_status())


def test_unknown_generator_is_reported_clearly():
    with pytest.raises(KeyError, match="unknown generator"):
        api.build("does-not-exist")


def test_analytic_volume_formula_is_self_consistent():
    p = BracketParams(width=80, depth=60, height=50, thickness=6, hole_diameter=8)
    holes = 4 * math.pi * 16 * 6
    assert bracket_volume(p) == pytest.approx(
        80 * 60 * 6 + 80 * 6 * 50 - 80 * 36 - holes
    )
