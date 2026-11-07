"""Portable catalog selection, discovery and machine-specific root bindings."""

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from cad_context import project_catalog as catalog
from cad_context import projects
from cad_context.cli import app


@pytest.fixture
def storage(tmp_path, monkeypatch, cache):
    root = tmp_path / "drive-a"
    root.mkdir()
    projects.initialise(root / "puzzle")
    projects.initialise(root / "another")
    # Listing must never execute Python.
    (root / "puzzle" / "__init__.py").write_text("raise RuntimeError('executed')")
    payload = {
        "version": 1,
        "default": "animal-puzzle",
        "roots": {"models": {"env": "CADCON_TEST_MODELS"}},
        "projects": {"animal-puzzle": {"root": "models", "path": "puzzle"}},
    }
    catalog.catalog_path().write_text(yaml.safe_dump(payload))
    monkeypatch.delenv("CADCON_TEST_MODELS", raising=False)
    monkeypatch.delenv(projects.PROJECT_ENV_VAR, raising=False)
    monkeypatch.delenv(projects.NO_PROJECT_ENV_VAR, raising=False)
    projects.configure_command_project(None)
    yield root
    projects.configure_command_project(None)


def test_default_and_local_binding_survive_cache_reset(storage):
    catalog.bind("models", storage)
    assert projects.active_path() == storage / "puzzle"
    rows = catalog.listing()["projects"]
    assert len(rows) == 2
    assert rows[0]["id"] == "animal-puzzle" and rows[0]["default"]
    assert rows[1]["id"] is None and rows[1]["available"]
    projects.clear()
    assert projects.active_path() == storage / "puzzle"
    projects.configure_command_project(None, disabled=True)
    assert projects.active_path() is None


def test_id_pointer_relocates_and_precedence(storage, tmp_path, monkeypatch):
    catalog.bind("models", storage)
    projects.persist(Path("animal-puzzle"))
    assert json.loads(projects.pointer_path().read_text())["project"] == "animal-puzzle"
    other = tmp_path / "drive-b"
    projects.initialise(other / "puzzle")
    monkeypatch.setenv("CADCON_TEST_MODELS", str(other))
    assert projects.active_path() == other / "puzzle"
    monkeypatch.setenv(projects.PROJECT_ENV_VAR, str(storage / "another"))
    assert projects.active_path() == storage / "another"
    projects.configure_command_project(Path("animal-puzzle"))
    assert projects.active_path() == other / "puzzle"


def test_missing_root_list_and_recovery_cli(storage):
    runner = CliRunner()
    rows = catalog.listing()["projects"]
    assert not rows[0]["available"]
    with pytest.raises(projects.ProjectError, match="project root models"):
        projects.active_path()
    assert runner.invoke(app, ["project", "list"]).exit_code == 0
    assert (
        runner.invoke(app, ["project", "root", "models", str(storage)]).exit_code == 0
    )
    assert runner.invoke(app, ["project", "use", "animal-puzzle"]).exit_code == 0
    result = runner.invoke(app, ["--project", "animal-puzzle", "project", "info"])
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize("path", ["../escape", "/absolute", "C:/absolute", "a\\b"])
def test_catalog_rejects_unconfined_paths(path):
    with pytest.raises(ValueError):
        catalog.Entry(root="models", path=path)


def test_candidates_missing_project_and_bad_manifest(storage):
    raw = yaml.safe_load(catalog.catalog_path().read_text())
    raw["roots"]["models"]["candidates"] = [str(storage)]
    catalog.catalog_path().write_text(yaml.safe_dump(raw))
    assert projects.active_path() == storage / "puzzle"
    (storage / "puzzle" / "project.yaml").write_text("bad: manifest")
    assert not catalog.listing()["projects"][0]["available"]
    (storage / "puzzle" / "project.yaml").unlink()
    with pytest.raises(projects.ProjectError, match="has no project.yaml"):
        projects.active_path()


def test_ambiguous_candidates_require_binding(storage, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    declaration = catalog.Catalog(
        roots={"models": {"candidates": [str(storage), str(other)]}}
    )
    with pytest.raises(projects.ProjectError, match="ambiguous"):
        catalog.resolve_root("models", declaration)


def test_discovery_only_includes_explicit_valid_cadcon_projects(storage):
    catalog.bind("models", storage)
    unrelated = storage / "characters-generation"
    unrelated.mkdir()
    (unrelated / "project.yaml").write_text("name: characters-generation\n")
    invalid = storage / "broken-cadcon"
    invalid.mkdir()
    (invalid / "project.yaml").write_text("tool: cadcon\nunknown: field\n")
    malformed = storage / "malformed"
    malformed.mkdir()
    (malformed / "project.yaml").write_text("[unterminated")
    (storage / "ordinary-folder").mkdir()
    rows = catalog.listing()["projects"]
    assert {Path(row["path"]).name for row in rows} == {"puzzle", "another"}
    # Explicitly cataloged legacy manifests remain compatible.
    manifest = storage / "puzzle" / "project.yaml"
    manifest.write_text("version: 1\nname: legacy\n")
    assert catalog.listing()["projects"][0]["available"]
