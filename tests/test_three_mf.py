"""Actual 3MF package, topology, atomicity and CLI delivery proof."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import pytest
import yaml
from typer.testing import CliRunner

from cad_context import api, exchange, projects, workspace
from cad_context.cli import app
from cad_context.exchange import three_mf
from cad_context.types import BackendUnavailable, BuildResult

pytestmark = pytest.mark.usefixtures("cache")
runner = CliRunner()


@pytest.fixture()
def box():
    from build123d import Align, Box

    return BuildResult(
        "bracket-build123d",
        "build123d",
        "3d",
        {},
        Box(13, 17, 23, align=(Align.MIN,) * 3),
        {
            "volume": 5083,
            "volume_analytic": 5083,
            "bounds_min": [0, 0, 0],
            "bounds_max": [13, 17, 23],
        },
    )


@pytest.fixture()
def artifact(tmp_path, box):
    return exchange.export(box, ["3mf"], out_dir=tmp_path)["files"]["3mf"]


def rewrite(path, change):
    with ZipFile(path) as archive:
        contents = {name: archive.read(name) for name in archive.namelist()}
    name = next(n for n in contents if n.endswith(".model"))
    root = ET.fromstring(contents[name])
    change(root)
    contents[name] = ET.tostring(root)
    with ZipFile(path, "w") as archive:
        for name, content in contents.items():
            archive.writestr(name, content)


def test_asymmetric_round_trip_and_lib3mf_read(artifact):
    from build123d import Mesher, Unit

    metrics = three_mf.read_metrics(artifact)
    assert all(metrics["checks"].values())
    assert metrics["volume"] == pytest.approx(5083, rel=0.01)
    assert metrics["bounds_min"] == pytest.approx([0, 0, 0], abs=1e-6)
    assert metrics["bounds_max"] == pytest.approx([13, 17, 23], abs=1e-6)
    assert metrics["mesh_objects"] == metrics["build_items"] == 1
    assert metrics["vertices"] == 8 and metrics["faces"] == 12
    reader = Mesher(Unit.MM)
    assert len(reader.read(artifact)) == 1
    assert reader.model_unit == Unit.MM and reader.mesh_count == 1


def test_instance_transform_applied_once(artifact):
    def move(root):
        root.find(f"{three_mf.CORE}build/{three_mf.CORE}item").set(
            "transform", "1 0 0 0 1 0 0 0 1 5 7 11"
        )

    rewrite(artifact, move)
    metrics = three_mf.read_metrics(artifact)
    assert metrics["bounds_min"] == pytest.approx([5, 7, 11])
    assert metrics["bounds_max"] == pytest.approx([18, 24, 34])
    assert metrics["volume"] == pytest.approx(5083)


@pytest.mark.parametrize(
    "fault",
    [
        "units",
        "build_count",
        "object_count",
        "reference",
        "component",
        "indices",
        "nan",
        "transform",
        "duplicate_id",
    ],
)
def test_malformed_packages_fail(artifact, fault):
    def damage(root):
        c = three_mf.CORE
        item = root.find(f"{c}build/{c}item")
        obj = root.find(f"{c}resources/{c}object")
        if fault == "units":
            root.set("unit", "inch")
        elif fault == "build_count":
            root.find(f"{c}build").append(ET.fromstring(ET.tostring(item)))
        elif fault in {"object_count", "duplicate_id"}:
            copy = ET.fromstring(ET.tostring(obj))
            if fault == "object_count":
                copy.set("id", "999")
            root.find(f"{c}resources").append(copy)
        elif fault == "reference":
            item.set("objectid", "999")
        elif fault == "component":
            root.find(f".//{c}component").set("objectid", "999")
        elif fault == "indices":
            root.find(f".//{c}triangle").set("v1", "999999")
        elif fault == "nan":
            root.find(f".//{c}vertex").set("x", "nan")
        elif fault == "transform":
            item.set("transform", "1 2 3")

    rewrite(artifact, damage)
    with pytest.raises(ValueError):
        three_mf.read_metrics(artifact)


@pytest.mark.parametrize(
    "fault,check",
    [
        ("duplicate", "no_duplicate_faces"),
        ("degenerate", "no_degenerate_faces"),
        ("reverse_one", "winding_consistent"),
        ("reverse_all", "positive_volume"),
        ("open", "watertight"),
        ("disconnected", "connected"),
    ],
)
def test_bad_topology_is_detected(artifact, fault, check):
    def damage(root):
        c = three_mf.CORE
        triangles = root.find(f".//{c}triangles")
        if fault == "duplicate":
            triangles.append(ET.fromstring(ET.tostring(triangles[0])))
        elif fault == "degenerate":
            triangles[0].set("v2", triangles[0].get("v1"))
        elif fault.startswith("reverse"):
            for t in list(triangles) if fault == "reverse_all" else [triangles[0]]:
                a, b = t.get("v1"), t.get("v2")
                t.set("v1", b)
                t.set("v2", a)
        elif fault == "open":
            triangles.remove(triangles[0])
        else:
            vertices = root.find(f".//{c}vertices")
            count = len(vertices)
            for vertex in list(vertices):
                copy = ET.fromstring(ET.tostring(vertex))
                copy.set("x", str(float(copy.get("x")) + 100))
                vertices.append(copy)
            for triangle in list(triangles):
                copy = ET.fromstring(ET.tostring(triangle))
                for key in ("v1", "v2", "v3"):
                    copy.set(key, str(int(copy.get(key)) + count))
                triangles.append(copy)

    rewrite(artifact, damage)
    assert not three_mf.read_metrics(artifact)["checks"][check]


def test_multisolid_and_bad_topology_preserve_previous_file(artifact, box, monkeypatch):
    from build123d import Compound, Pos

    original = artifact.read_bytes()
    box.native = Compound(children=[box.native, Pos(100, 0, 0) * box.native])
    with pytest.raises(ValueError, match="exactly one solid"):
        exchange.export(box, ["3mf"], out_dir=artifact.parent)
    assert artifact.read_bytes() == original
    box.native = box.native.solids()[0]
    monkeypatch.setattr(
        three_mf, "read_metrics", lambda _: {"checks": {"watertight": False}}
    )
    with pytest.raises(ValueError, match="topology failed"):
        exchange.export(box, ["3mf"], out_dir=artifact.parent, measure=False)
    assert artifact.read_bytes() == original
    assert list(artifact.parent.iterdir()) == [artifact]


def test_required_missing_3mf_is_failed_not_all_passed(monkeypatch):
    def unavailable(*args):
        raise BackendUnavailable("lib3mf unavailable")

    monkeypatch.setattr(three_mf, "write", unavailable)
    result = runner.invoke(
        app, ["--no-project", "verify", "bracket-build123d", "-f", "3mf"]
    )
    assert result.exit_code == 1
    payload = json.loads(
        (workspace.results_dir() / "verify-bracket-build123d.json").read_text()
    )
    assert payload["status"] == "error"
    assert payload["data"]["checks"]["3mf_artifact_present"] is False
    assert "3mf" in payload["data"]["skipped"]


def test_3mf_cli_generation_and_verification():
    for command in ("generate", "verify"):
        result = runner.invoke(
            app, ["--no-project", command, "bracket-build123d", "-f", "3mf"]
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(
            (workspace.results_dir() / f"{command}-bracket-build123d.json").read_text()
        )
        assert payload["status"] == "ok"
        assert payload["data"]["measurements"]["3mf"]["watertight"]
        assert set(payload["data"]["files"]) == {"3mf"}


def test_external_project_separate_pieces(tmp_path, monkeypatch):
    root = tmp_path / "pieces"
    root.mkdir()
    declarations = []
    for index, name in enumerate(("piece-one", "piece-two"), start=1):
        module = name.replace("-", "_")
        declarations.append(
            dict(
                id=name,
                title=name,
                kind="3d",
                backend="build123d",
                module=module,
                params_model="Params",
                formats=["3mf"],
            )
        )
        (root / f"{module}.py").write_text(
            f"""
from cad_context.params import ShapeParams
from cad_context.types import BuildResult
class Params(ShapeParams):
    pass
def build(params):
    from build123d import Align, Box
    shape = Box({index * 13}, 17, 23, align=(Align.MIN,)*3)
    return BuildResult({name!r}, "build123d", "3d", {{}}, shape,
        {{"volume": shape.volume, "volume_analytic": {index * 5083},
          "bounds_min": [0,0,0], "bounds_max": [{index * 13},17,23]}})
""",
            encoding="utf-8",
        )
    (root / "project.yaml").write_text(
        yaml.safe_dump(dict(version=1, name="pieces", generators=declarations)),
        encoding="utf-8",
    )
    monkeypatch.delenv(projects.NO_PROJECT_ENV_VAR, raising=False)
    for declaration in declarations:
        name = declaration["id"]
        result = runner.invoke(app, ["--project", str(root), "verify", name])
        assert result.exit_code == 0, result.output
        path = root / "cad" / name / f"{name}.3mf"
        assert path.exists()
        summary = json.loads(path.with_name(f"{name}.measurements.json").read_text())
        assert summary["measurements"]["3mf"]["mesh_objects"] == 1
        assert summary["measurements"]["3mf"]["volume"] == pytest.approx(
            5083 * (1 if name == "piece-one" else 2)
        )
        assert path.resolve().is_relative_to(root.resolve())
    assert len(list(root.rglob("*.3mf"))) == 2
    assert not list(root.rglob("__pycache__"))
    projects.configure_command_project(None)


def test_mesh_proof_does_not_use_accompanying_stl(tmp_path):
    exported = exchange.export(
        api.build("bracket-build123d"), ["stl", "3mf"], out_dir=tmp_path
    )
    assert exported["measurements"]["3mf"]["volume"] == pytest.approx(
        exported["measurements"]["mesh"]["volume"], rel=0.01
    )
    exported["files"]["stl"].unlink()
    assert all(three_mf.read_metrics(exported["files"]["3mf"])["checks"].values())


def test_malformed_geometry_is_not_optional_skip(tmp_path, box, monkeypatch):
    from build123d import Mesher

    def invalid(*args, **kwargs):
        raise RuntimeError("3mf mesh is invalid")

    monkeypatch.setattr(Mesher, "add_shape", invalid)
    with pytest.raises(ValueError, match="3MF export failed"):
        exchange.export(box, ["3mf"], out_dir=tmp_path)
    assert not list(tmp_path.glob("*.3mf"))


def test_extra_geometry_is_not_silently_dropped(tmp_path, box):
    from build123d import Compound, Edge

    box.native = Compound(children=[box.native, Edge.make_line((0, 0, 0), (100, 0, 0))])
    with pytest.raises(ValueError, match="extra shells, faces or wires"):
        exchange.export(box, ["3mf"], out_dir=tmp_path)


@pytest.mark.parametrize(
    "formats,backend,kind",
    [
        (["3mf"], "openscad", "3d"),
        (["3mf"], "shapely", "2d"),
        (["unknown"], "build123d", "3d"),
    ],
)
def test_project_format_validation(formats, backend, kind):
    with pytest.raises(ValueError):
        projects.ProjectManifest.model_validate(
            dict(
                name="bad-formats",
                generators=[
                    dict(
                        id="piece",
                        title="piece",
                        kind=kind,
                        backend=backend,
                        module="piece",
                        params_model="Params",
                        formats=formats,
                    )
                ],
            )
        )


def test_verify_missing_step_fails(monkeypatch):
    original_export = exchange.export

    def missing_step(*args, **kwargs):
        exported = original_export(*args, **kwargs)
        exported["files"].pop("step", None)
        exported["measurements"].pop("step", None)
        exported["skipped"]["step"] = "runtime unavailable"
        return exported

    monkeypatch.setattr(exchange, "export", missing_step)
    result = runner.invoke(app, ["--no-project", "verify", "bracket-build123d"])
    assert result.exit_code == 1
    payload = json.loads(
        (workspace.results_dir() / "verify-bracket-build123d.json").read_text()
    )
    assert payload["data"]["checks"]["step_artifact_present"] is False


def test_verify_optional_openscad_renderer_degrades(tmp_path, monkeypatch, box):
    from types import SimpleNamespace

    from cad_context import generators
    from cad_context.generators.models import BracketParams

    spec = SimpleNamespace(
        backend="openscad",
        kind="3d",
        formats=("scad", "stl", "glb"),
        parse=lambda _: BracketParams(),
        build=lambda _: box,
    )
    monkeypatch.setattr(generators, "get", lambda _: spec)
    monkeypatch.setattr(
        exchange,
        "export",
        lambda *a, **kw: {
            "files": {"scad": tmp_path / "piece.scad"},
            "measurements": {},
            "skipped": {
                "stl": "OpenSCAD binary not found",
                "glb": "OpenSCAD binary not found",
            },
            "measurement_file": None,
        },
    )
    result = runner.invoke(app, ["--no-project", "verify", "piece"])
    assert result.exit_code == 0, result.output
    payload = json.loads((workspace.results_dir() / "verify-piece.json").read_text())
    assert payload["status"] == "degraded"
    assert all(payload["data"]["checks"].values())
def test_mesh_bounds_budget_is_translation_invariant():
    from cad_context.exchange.three_mf import bounds_match

    for shift in (0.0, 1000000.0, -1000000.0):
        low = [shift, 0, 0]
        high = [shift + 50, 40, 10]
        assert bounds_match([shift + 0.005, 0, 0], low, low, high)
        assert not bounds_match([shift + 0.02, 0, 0], low, low, high)


