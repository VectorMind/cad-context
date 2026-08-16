"""External project manifests, loading, selection, and output routing."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from cad_context import api, backends, exchange, generators, projects, workspace
from cad_context.cli import app
from cad_context.exchange import export3d

runner = CliRunner()


@pytest.fixture()
def sample_project(tmp_path, cache, monkeypatch):
    source = Path(__file__).parent / "fixtures" / "sample_project"
    target = tmp_path / "sample-project"
    shutil.copytree(source, target)
    monkeypatch.delenv(projects.PROJECT_ENV_VAR, raising=False)
    projects.configure_command_project(target)
    yield target
    projects.configure_command_project(None)


def test_project_manifest_merges_generators_without_importing_code(sample_project):
    listed = {row["id"]: row for row in api.generators()}
    assert listed["project-plate"]["origin"] == "project"
    assert listed["project-plate"]["project"] == "sample-project"
    assert listed["project-plate"]["exposure"]["editable"] == ["width"]
    assert not list(sample_project.rglob("__pycache__"))


def test_project_schema_defaults_and_artifacts_stay_with_project(sample_project):
    schema = api.schema("project-plate")
    defaults = {
        parameter["name"]: parameter["default"]
        for parameter in schema["parameters"]
    }
    assert defaults["width"] == 75.0

    built = api.build("project-plate")
    exported = exchange.export(built, ["svg", "dxf"])
    expected = sample_project / "cad" / "project-plate"
    assert set(exported["files"].values()) == {
        expected / "project-plate.svg",
        expected / "project-plate.dxf",
    }
    assert exported["measurement_file"] == expected / "project-plate.measurements.json"
    assert exported["measurement_file"].exists()
    assert not list(sample_project.rglob("__pycache__"))


def test_project_collision_stops_registry_loading(sample_project):
    manifest_path = sample_project / projects.MANIFEST_FILENAME
    payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    payload["generators"][0]["id"] = "plate2d"
    payload["exposure"]["plate2d"] = payload["exposure"].pop("project-plate")
    manifest_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(ValueError, match="collision.*plate2d"):
        generators.specs()


def test_project_use_requires_initialization_and_clear_is_explicit(tmp_path, cache):
    empty = tmp_path / "empty"
    empty.mkdir()
    failed = runner.invoke(app, ["project", "use", str(empty)])
    assert failed.exit_code == 1
    assert "project.yaml" in failed.output

    initialized = runner.invoke(app, ["project", "init", str(empty)])
    assert initialized.exit_code == 0, initialized.output
    selected = runner.invoke(app, ["project", "use", str(empty)])
    assert selected.exit_code == 0, selected.output
    pointer = json.loads(projects.pointer_path().read_text(encoding="utf-8"))
    assert pointer["project"] == str(empty.resolve())
    cleared = runner.invoke(app, ["project", "clear"])
    assert cleared.exit_code == 0
    assert not projects.pointer_path().exists()


def test_project_init_dry_run_does_not_write(tmp_path, cache):
    target = tmp_path / "future"
    result = runner.invoke(app, ["project", "init", str(target), "--dry-run"])
    assert result.exit_code == 0, result.output
    assert not target.exists()


@pytest.mark.skipif(not backends.available("openscad"), reason="openscad extra missing")
def test_project_openscad_generator_preserves_source_only_degradation(
    sample_project, monkeypatch
):
    monkeypatch.setattr(export3d, "openscad_executable", lambda: None)
    built = api.build("project-openscad-box")
    exported = exchange.export(built, ["scad", "stl", "glb"])
    assert exported["files"]["scad"].exists()
    assert "stl" not in exported["files"] and "glb" not in exported["files"]
    assert "OpenSCAD binary not found" in exported["skipped"]["stl"]


def test_explicit_no_project_bypasses_persisted_pointer(sample_project):
    projects.persist(sample_project)
    projects.configure_command_project(None)
    result = runner.invoke(app, ["--no-project", "generators"])
    assert result.exit_code == 0, result.output
    payload = json.loads(
        (workspace.results_dir() / "generators.json").read_text(encoding="utf-8")
    )
    assert "project-plate" not in {row["id"] for row in payload["data"]["generators"]}


def test_no_project_environment_prevents_child_process_pointer_fallback(
    sample_project, monkeypatch
):
    projects.persist(sample_project)
    projects.configure_command_project(None)
    monkeypatch.setenv(projects.NO_PROJECT_ENV_VAR, "1")
    assert projects.active_path() is None
