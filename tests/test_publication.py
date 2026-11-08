"""Project cache isolation, explicit consumer publication and recovery contracts."""

import json

import pytest
import yaml

from cad_context import project_catalog as catalog
from cad_context import projects, publication, workspace


def _visual_definition(root, output):
    folder = output / "evidence"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "trace.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 10">'
        '<path d="M0 0L20 10"/></svg>'
    )
    definition = {
        "title": "From sketch to model",
        "stages": [
            {
                "id": "trace",
                "title": "Source trace",
                "state": "history",
                "assets": [
                    {
                        "path": "evidence/trace.svg",
                        "location": "cache",
                        "title": "The reviewed line drawing",
                        "caption": "Original outline before rounding.",
                        "wide": True,
                    }
                ],
            }
        ],
    }
    (root / "presentation.yaml").write_text(yaml.safe_dump(definition))
    return definition


@pytest.fixture
def model(tmp_path, cache):
    sources = tmp_path / "sources"
    root = sources / "puzzle"
    root.mkdir(parents=True)
    drive = tmp_path / "drive"
    drive.mkdir()
    manifest = {
        "id": "puzzle",
        "name": "Puzzle",
        "tool": "cadcon",
        "generators": [
            {
                "id": "piece",
                "title": "Piece",
                "kind": "3d",
                "backend": "build123d",
                "module": "builder",
                "params_model": "Params",
                "formats": ["glb", "3mf"],
            }
        ],
        "web_models": {"animal": "piece"},
        "print_models": {"head": "piece"},
    }
    (root / "project.yaml").write_text(yaml.safe_dump(manifest))
    (root / "builder.py").write_text("# durable source\n")
    (root / "reference.png").write_bytes(b"reference")
    (root / "obsolete.stl").write_bytes(b"not a source")
    catalog.catalog_path().write_text(
        yaml.safe_dump(
            {
                "roots": {
                    "source": {"candidates": [str(sources)]},
                    "drive": {"candidates": [str(drive)]},
                },
                "projects": {
                    "puzzle": {
                        "root": "source",
                        "path": "puzzle",
                        "publication": {"root": "drive", "path": "puzzle"},
                    }
                },
            }
        )
    )
    projects.configure_command_project(root)
    output = workspace.project_cache(root)
    folder = output / "cad/piece"
    folder.mkdir(parents=True)
    for ext in ("glb", "3mf"):
        (folder / f"piece.{ext}").write_bytes(ext.encode())
    proof = {
        "verified": True,
        "source_identity": publication.source_identity(root),
        "artifacts": {
            p.relative_to(output).as_posix(): publication.digest(p)
            for p in folder.iterdir()
        },
    }
    (output / "rebuild.json").write_text(json.dumps(proof))
    yield root, drive / "puzzle", output
    projects.configure_command_project(None)


def test_projects_generate_only_inside_redirected_cache(model, cache):
    root, _, output = model
    spec = projects.project_specs()[0]
    assert spec.artifact_root == output / "cad"
    assert spec.artifact_root.is_relative_to(cache)
    assert not (root / "cad").exists()


def test_visual_publication_preserves_geometry_and_survives_source_cache_loss(model):
    import shutil
    import zipfile

    from cad_context import presentation

    root, drive, output = model
    publication.publish("puzzle")
    publication.release("puzzle", "2026-11-08", freeze=True)
    geometry = (drive / "web/latest/manifest.json").read_bytes()
    release = (drive / "3d-print/2026-11-08/release.json").read_bytes()
    source_identity = publication.source_identity(root)
    generation_identity = publication.generation_identity(root)
    _visual_definition(root, output)
    assert publication.source_identity(root) == source_identity
    assert publication.generation_identity(root) == generation_identity
    result = presentation.present("puzzle")
    assert result["asset_count"] == 1
    assert (drive / "web/gallery/latest/trace/trace.svg").is_file()
    assert (drive / "web/latest/manifest.json").read_bytes() == geometry
    assert (drive / "3d-print/2026-11-08/release.json").read_bytes() == release
    assert publication._verified(root)["verified"]
    (drive / "web/gallery/latest").chmod(0o555)
    presentation.present("puzzle")
    assert not (drive / "web/gallery/.latest-previous").exists()
    with zipfile.ZipFile(drive / "reference/source.zip") as archive:
        assert "presentation.yaml" in archive.namelist()
    assert (
        json.loads((drive / "reference/source.json").read_text())["source_identity"]
        == source_identity
    )
    shutil.rmtree(output)
    shutil.rmtree(root)
    assert (
        publication.view("puzzle")["presentation"]["stages"][0]["assets"][0]["title"]
        == "The reviewed line drawing"
    )


def test_missing_visual_refuses_replacement_of_shared_gallery(model):
    from cad_context import presentation

    root, drive, output = model
    definition = _visual_definition(root, output)
    presentation.present("puzzle")
    before = (drive / "web/gallery/latest/manifest.json").read_bytes()
    definition["stages"][0]["assets"][0]["path"] = "evidence/missing.svg"
    (root / "presentation.yaml").write_text(yaml.safe_dump(definition))
    with pytest.raises(projects.ProjectError, match="missing visual asset"):
        presentation.present("puzzle")
    assert (drive / "web/gallery/latest/manifest.json").read_bytes() == before


@pytest.mark.parametrize("path", ["../secret.png", "builder.py", "c:/secret.svg"])
def test_visual_asset_paths_are_confined_and_images_only(path):
    from pydantic import ValidationError

    from cad_context.presentation import Visual

    with pytest.raises(ValidationError):
        Visual(path=path, title="Invalid asset")


def test_visual_publication_retries_a_transient_directory_lock(tmp_path, monkeypatch):
    from pathlib import Path

    from cad_context import presentation

    source = tmp_path / "stage"
    source.mkdir()
    (source / "image.svg").write_text("image")
    target = tmp_path / "latest"
    original = Path.rename
    attempts = []

    def locked_once(path, destination):
        attempts.append(path)
        if len(attempts) == 1:
            raise PermissionError("Drive is indexing a new folder")
        return original(path, destination)

    monkeypatch.setattr(Path, "rename", locked_once)
    monkeypatch.setattr(presentation.time, "sleep", lambda _: None)
    presentation._rename(source, target)
    assert (target / "image.svg").read_text() == "image"
    assert len(attempts) == 2


def test_publish_survives_cache_loss_and_restore_preserves_source(model, tmp_path):
    root, drive, output = model
    publication.publish("puzzle")
    assert (drive / "web/latest/animal.glb").read_bytes() == b"glb"
    assert not list(drive.rglob("*.3mf"))  # publishing is never a print release
    import shutil

    shutil.rmtree(output)
    assert publication.view("puzzle")["published"]["models"][0]["id"] == "animal"
    restored = tmp_path / "restored"
    publication.restore("puzzle", restored)
    assert (restored / "builder.py").read_bytes() == (root / "builder.py").read_bytes()
    assert (restored / "reference.png").is_file()
    assert not (restored / "obsolete.stl").exists()
    with pytest.raises(projects.ProjectError, match="must not exist"):
        publication.restore("puzzle", restored)


def test_stale_source_and_changed_exports_cannot_publish(model):
    root, _, output = model
    (root / "builder.py").write_text("# changed\n")
    with pytest.raises(projects.ProjectError, match="source changed"):
        publication.publish("puzzle")
    (root / "builder.py").write_text("# durable source\n")
    (output / "cad/piece/piece.glb").write_bytes(b"corrupt")
    with pytest.raises(projects.ProjectError, match="artifacts changed"):
        publication.publish("puzzle")


def test_republish_cleans_read_only_drive_folder(model):
    _, drive, _ = model
    publication.publish("puzzle")
    (drive / "web/latest").chmod(0o555)
    publication.publish("puzzle")
    assert (drive / "web/latest/animal.glb").read_bytes() == b"glb"
    assert not (drive / "web/.latest-previous").exists()


def test_dated_releases_are_explicit_and_never_overwritten(model):
    _, drive, _ = model
    result = publication.release("puzzle", "2026-11-08")
    assert result["status"] == "draft"
    assert result["generators"] == {"head.3mf": "piece"}
    assert (drive / "3d-print/2026-11-08/head.3mf").is_file()
    assert publication.freeze("puzzle", "2026-11-08")["status"] == "frozen"
    with pytest.raises(projects.ProjectError, match="already exists"):
        publication.release("puzzle", "2026-11-08")
    with pytest.raises(projects.ProjectError, match="release name"):
        publication.release("puzzle", "../escape")


def test_release_provenance_is_compared_with_published_source(model):
    root, drive, _ = model
    publication.publish("puzzle")
    publication.release("puzzle", "2026-11-08")
    assert (
        publication.view("puzzle")["releases"][0]["published_source_relation"]
        == "same-source"
    )
    manifest_path = drive / "web/latest/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["source_identity"] = "newer-source"
    manifest_path.write_text(json.dumps(manifest))
    assert (
        publication.view("puzzle")["releases"][0]["published_source_relation"]
        == "different-source"
    )
    legacy = drive / "3d-print/2026-10-25"
    legacy.mkdir()
    (legacy / "release.json").write_text(
        json.dumps({"status": "legacy-frozen", "files": {"old.3mf": "old-hash"}})
    )
    assert (
        publication.view("puzzle")["releases"][1]["published_source_relation"]
        == "legacy-untracked"
    )
    manifest_path.unlink()
    assert (
        publication.view("puzzle")["releases"][0]["published_source_relation"]
        == "no-published-source"
    )


def test_corrupt_recovery_snapshot_is_rejected_without_destination(model, tmp_path):
    _, drive, _ = model
    publication.snapshot("puzzle")
    (drive / "reference/source.zip").write_bytes(b"broken")
    target = tmp_path / "should-not-exist"
    with pytest.raises(projects.ProjectError, match="checksum"):
        publication.restore("puzzle", target)
    assert not target.exists()


def test_published_view_and_restore_work_without_local_source(model, tmp_path):
    root, _, _ = model
    publication.publish("puzzle")
    root.rename(tmp_path / "source-offline")
    assert publication.view("puzzle")["published"]["name"] == "Puzzle"
    restored = tmp_path / "new-machine"
    publication.restore("puzzle", restored)
    assert (restored / "builder.py").is_file()


def test_other_machine_source_update_is_not_silently_overwritten(model):
    _, drive, _ = model
    publication.snapshot("puzzle")
    path = drive / "reference/source.json"
    changed = json.loads(path.read_text())
    changed["snapshot_identity"] = "other-machine"
    path.write_text(json.dumps(changed))
    with pytest.raises(projects.ProjectError, match="shared source changed"):
        publication.snapshot("puzzle")


def test_invalid_calendar_date_is_rejected(model):
    with pytest.raises(projects.ProjectError, match="invalid release date"):
        publication.release("puzzle", "2026-99-01")


def test_resume_requires_verified_unchanged_generator_source(model):
    root, _, _ = model
    publication.checkpoint_exports(root, verified=False)
    with pytest.raises(projects.ProjectError, match="not verified"):
        publication.rebuild(root, reuse_exports=True)
    publication.checkpoint_exports(root)
    (root / "builder.py").write_text("# changed root-level generator\n")
    with pytest.raises(projects.ProjectError, match="generator source changed"):
        publication.rebuild(root, reuse_exports=True)
