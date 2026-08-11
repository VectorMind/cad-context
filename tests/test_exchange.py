"""Export proof: files exist, load back, and measure within tolerance."""

from __future__ import annotations

import pytest

from cad_context import api, backends, exchange, workspace
from cad_context.exchange import export2d, export3d
from cad_context.generators.models import BracketParams, bracket_volume

#: Tessellated meshes and faceted CSG never match the exact solid; 1% is the
#: repository's cross-backend agreement budget.
VOLUME_TOLERANCE = 0.01


def test_fixed_destination_is_stable_and_inside_the_cache(cache):
    first = exchange.destination("bracket-cadquery", "stl")
    second = exchange.destination("bracket-cadquery", "stl")
    assert first == second
    assert first.name == "bracket-cadquery.stl"
    assert workspace.cad_dir() in first.parents


def test_out_dir_overrides_the_fixed_path(tmp_path):
    path = exchange.destination("plate2d", "svg", tmp_path)
    assert path == tmp_path / "plate2d.svg"


def test_unknown_format_is_rejected():
    result = api.build("plate2d") if backends.available("shapely") else None
    if result is None:
        pytest.skip("vector2d extra missing")
    with pytest.raises(ValueError, match="unknown format"):
        exchange.export(result, ["pdf"])


@pytest.mark.skipif(not backends.available("shapely"), reason="vector2d extra missing")
def test_2d_exports_round_trip(tmp_path):
    build_result = api.build("plate2d", width=140.0, slot_count=4)
    exported = exchange.export(build_result, ["svg", "dxf"], out_dir=tmp_path)

    assert set(exported["files"]) == {"svg", "dxf"}
    assert not exported["skipped"]
    for path in exported["files"].values():
        assert path.exists() and path.stat().st_size > 0

    dxf = export2d.read_dxf_metrics(exported["files"]["dxf"])
    assert dxf["units_name"] == "mm"
    assert dxf["polylines"] == 1 + 4 + 4  # outline + slots + corner holes
    assert dxf["bounds"] == pytest.approx([0.0, 0.0, 140.0, 80.0], abs=1e-6)

    svg = export2d.read_svg_metrics(exported["files"]["svg"])
    assert svg["has_viewbox"] and svg["paths"] == 1


def test_3d_exports_round_trip_and_measure(tmp_path, bracket_3d):
    params = {"width": 90.0}
    build_result = api.build(bracket_3d, **params)
    spec_formats = [
        f
        for f in exchange.FORMAT_ORDER
        if f in set(api.schema(bracket_3d)["formats"])
    ]
    exported = exchange.export(build_result, spec_formats, out_dir=tmp_path)

    assert "stl" in exported["files"], exported["skipped"]
    assert "glb" in exported["files"], exported["skipped"]
    for path in exported["files"].values():
        assert path.exists() and path.stat().st_size > 0

    expected = bracket_volume(BracketParams(**params))
    mesh = exported["measurements"]["mesh"]
    assert mesh["watertight"] is True
    assert mesh["volume"] == pytest.approx(expected, rel=VOLUME_TOLERANCE)
    assert mesh["bounds_min"] == pytest.approx([0.0, 0.0, 0.0], abs=1e-6)
    assert mesh["bounds_max"] == pytest.approx([90.0, 60.0, 50.0], abs=1e-6)

    glb = export3d.mesh_metrics(exported["files"]["glb"])
    assert glb["volume"] == pytest.approx(mesh["volume"], rel=1e-6)


def test_glb_alone_tessellates_without_leaving_an_stl(tmp_path, bracket_3d):
    build_result = api.build(bracket_3d)
    exported = exchange.export(build_result, ["glb"], out_dir=tmp_path)

    assert set(exported["files"]) == {"glb"}, exported["skipped"]
    assert sorted(p.name for p in tmp_path.iterdir()) == [f"{bracket_3d}.glb"]
    assert exported["measurements"]["mesh"]["volume"] == pytest.approx(
        bracket_volume(BracketParams()), rel=VOLUME_TOLERANCE
    )


@pytest.mark.skipif(
    not (backends.available("cadquery") or backends.available("build123d")),
    reason="no B-rep backend installed",
)
def test_step_round_trips_through_a_kernel(tmp_path):
    generator = (
        "bracket-cadquery" if backends.available("cadquery") else "bracket-build123d"
    )
    build_result = api.build(generator, width=90.0)
    exported = exchange.export(build_result, ["step"], out_dir=tmp_path, measure=False)
    metrics = export3d.read_step_metrics(exported["files"]["step"])
    assert metrics["volume"] == pytest.approx(
        bracket_volume(BracketParams(width=90.0)), rel=1e-6
    )


@pytest.mark.skipif(not backends.available("openscad"), reason="openscad extra missing")
def test_openscad_degrades_to_source_when_the_binary_is_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(export3d, "openscad_executable", lambda: None)
    build_result = api.build("bracket-openscad")
    exported = exchange.export(build_result, ["scad", "stl", "glb"], out_dir=tmp_path)

    assert exported["files"]["scad"].exists()
    assert "stl" not in exported["files"] and "glb" not in exported["files"]
    assert "OpenSCAD binary not found" in exported["skipped"]["stl"]
    assert "cylinder" in exported["files"]["scad"].read_text(encoding="utf-8")
