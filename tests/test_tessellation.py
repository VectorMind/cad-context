"""Quality profiles reach real mesh exports while preserving native geometry."""

from pathlib import Path

import pytest

from cad_context import api, exchange
from cad_context.exchange import export3d
from cad_context.types import Tessellation

pytestmark = pytest.mark.usefixtures("cache")


@pytest.mark.parametrize("value", [0, -0.1, float("nan"), float("inf")])
def test_invalid_tessellation_rejected(value):
    with pytest.raises(ValueError, match="finite and positive"):
        Tessellation(linear_deflection=value)
    with pytest.raises(ValueError, match="finite and positive"):
        Tessellation(angular_deflection=value)


def test_unknown_stl_writer_rejected():
    with pytest.raises(ValueError, match="stl_writer"):
        Tessellation(stl_writer="unknown")


def test_missing_mesher_runtime_reports_explicit_skipped_formats(monkeypatch, tmp_path):
    import build123d

    built = api.build("bracket-build123d")
    built.tessellation = Tessellation(stl_writer="mesher")

    def missing_runtime(**kwargs):
        raise OSError("test runtime absent")

    monkeypatch.setattr(build123d, "Mesher", missing_runtime)
    output = exchange.export(built, ["stl", "glb"], out_dir=tmp_path)
    assert not output["files"]
    assert set(output["skipped"]) == {"stl", "glb"}
    assert all("runtime unavailable" in reason for reason in output["skipped"].values())


def test_mesher_stl_and_glb_use_native_writer_without_changing_solid(
    monkeypatch, tmp_path
):
    import build123d

    built = api.build("bracket-build123d")
    expected_volume = built.native.volume
    built.tessellation = Tessellation(stl_writer="mesher")

    def unexpected_writer(*args, **kwargs):
        raise AssertionError("Mesher selection used the OCCT STL writer")

    monkeypatch.setattr(build123d, "export_stl", unexpected_writer)
    output = exchange.export(built, ["stl", "glb"], out_dir=tmp_path)
    assert set(output["files"]) == {"stl", "glb"}
    assert not output["skipped"]
    assert output["measurements"]["mesh"]["watertight"]
    assert output["measurements"]["mesh"]["volume"] == pytest.approx(
        expected_volume, rel=0.01
    )
    glb = export3d.mesh_metrics(output["files"]["glb"])
    assert glb["watertight"]
    assert glb["volume"] == pytest.approx(expected_volume, rel=0.01)
    assert built.native.volume == expected_volume
    assert built.summary()["tessellation"]["stl_writer"] == "mesher"


@pytest.mark.parametrize("profile", [None, Tessellation(0.005, 0.08)])
def test_quality_reaches_stl_and_actual_3mf(profile, monkeypatch, tmp_path):
    import build123d

    built = api.build("bracket-build123d")
    volume = built.native.volume
    built.tessellation = profile
    calls = []
    original = build123d.Mesher.add_shape

    def observe(self, shape, **kwargs):
        calls.append(kwargs)
        return original(self, shape, **kwargs)

    monkeypatch.setattr(build123d.Mesher, "add_shape", observe)
    output = exchange.export(built, ["3mf"], out_dir=tmp_path, measure=True)
    expected = profile or Tessellation()
    assert calls[0]["linear_deflection"] == expected.linear_deflection
    assert calls[0]["angular_deflection"] == expected.angular_deflection
    assert all(output["measurements"]["3mf"]["checks"].values())
    assert built.native.volume == volume
    assert built.summary()["tessellation"] == (
        {"linear_deflection": 0.005, "angular_deflection": 0.08} if profile else None
    )

    stl_calls = []

    def observe_stl(shape, filename, **kwargs):
        stl_calls.append(kwargs)
        Path(filename).write_bytes(b"quality propagation probe")

    monkeypatch.setattr(build123d, "export_stl", observe_stl)
    export3d.write_stl(built, tmp_path / "probe.stl")
    assert stl_calls[0]["tolerance"] == expected.linear_deflection
    assert stl_calls[0]["angular_tolerance"] == expected.angular_deflection
