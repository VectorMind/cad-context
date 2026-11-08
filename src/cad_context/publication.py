"""Disposable local builds, portable source recovery, explicit consumer publication."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

from . import project_catalog as catalog
from . import projects, workspace

GEOMETRY = {".step", ".stp", ".stl", ".glb", ".3mf"}
IGNORED = {
    ".git",
    ".cache",
    "__pycache__",
    "cad",
    "3d-print",
    ".venv",
    "node_modules",
    ".aws",
    ".ssh",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(root: Path) -> list[Path]:
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and not any(s in IGNORED for s in p.relative_to(root).parts)
        and (
            p.suffix.lower() not in GEOMETRY
            or p.relative_to(root).parts[0] in ("inputs", "references")
        )
        and p.name != "desktop.ini"
        and p.name != ".publication-base.json"
        and p.name != ".env"
        and not p.name.startswith(".env.")
        and not p.is_symlink()
    )


def source_identity(root: Path) -> str:
    values = {
        p.relative_to(root).as_posix(): digest(p)
        for p in source_files(root)
        if p.suffix.lower() != ".md"
        and p.relative_to(root).as_posix() != "presentation.yaml"
    }
    return hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()


def location(project_id: str) -> Path:
    entry = catalog.load().projects.get(project_id)
    if entry is None:
        raise projects.ProjectError(f"unknown project: {project_id}")
    declaration = entry.publication
    if declaration is None:
        local = catalog.resolve(project_id)
        declaration = projects.load_manifest(local).publication
    if declaration is None:
        raise projects.ProjectError(f"{project_id}: no publication location configured")
    parent = catalog.resolve_root(declaration.root, catalog.load())
    if parent is None:
        raise projects.ProjectError(f"publication root unavailable: {declaration.root}")
    target = (parent / declaration.path).resolve()
    if not target.is_relative_to(parent):
        raise projects.ProjectError("publication escapes configured root")
    return target


def _json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _remove_publication_tree(path: Path, parent: Path) -> None:
    """Remove only a confined staging tree, including Drive's read-only folders."""
    boundary = path.resolve()
    if path.is_symlink() or boundary.parent != parent.resolve():
        raise projects.ProjectError("publication cleanup escapes its parent")

    def retry_writable(operation, name, failure):
        target = Path(name)
        if not isinstance(failure[1], PermissionError) or not (
            target.resolve() == boundary or target.resolve().is_relative_to(boundary)
        ):
            raise failure[1]
        target.chmod(0o700)
        operation(name)

    shutil.rmtree(path, onerror=retry_writable)


def snapshot(project_id: str) -> dict:
    root = catalog.resolve(project_id)
    destination = location(project_id) / "reference"
    destination.mkdir(parents=True, exist_ok=True)
    _check_snapshot_base(root, destination)
    files = source_files(root)
    hashes = {p.relative_to(root).as_posix(): digest(p) for p in files}
    temporary = destination / "source.tmp.zip"
    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in files:
            archive.write(p, p.relative_to(root).as_posix())
    with zipfile.ZipFile(temporary) as archive:
        assert all(
            hashlib.sha256(archive.read(n)).hexdigest() == h for n, h in hashes.items()
        )
    temporary.replace(destination / "source.zip")
    result = {
        "project_id": project_id,
        "source_identity": hashlib.sha256(
            json.dumps(
                {
                    n: h
                    for n, h in hashes.items()
                    if Path(n).suffix.lower() != ".md" and n != "presentation.yaml"
                },
                sort_keys=True,
            ).encode()
        ).hexdigest(),
        "files": hashes,
        "snapshot_identity": hashlib.sha256(
            json.dumps(hashes, sort_keys=True).encode()
        ).hexdigest(),
        "archive_sha256": digest(destination / "source.zip"),
        "git_note": "Working source snapshot; no Git commit implied.",
    }
    _json(destination / "source.json", result)
    _json(
        root / ".publication-base.json",
        {
            "source_identity": result["source_identity"],
            "snapshot_identity": result["snapshot_identity"],
        },
    )
    return {
        "project_id": project_id,
        "archive": str(destination / "source.zip"),
        "files": len(files),
        "source_identity": result["source_identity"],
    }


def _check_snapshot_base(root: Path, reference: Path) -> None:
    """Refuse to silently replace another machine's newer source snapshot."""
    remote = reference / "source.json"
    if not remote.exists():
        return
    shared = json.loads(remote.read_text())
    key = "snapshot_identity" if "snapshot_identity" in shared else "source_identity"
    identity = shared[key]
    base = root / ".publication-base.json"
    expected = (
        json.loads(base.read_text()).get(
            key, json.loads(base.read_text())["source_identity"]
        )
        if base.exists()
        else (
            hashlib.sha256(
                json.dumps(
                    {
                        p.relative_to(root).as_posix(): digest(p)
                        for p in source_files(root)
                    },
                    sort_keys=True,
                ).encode()
            ).hexdigest()
            if key == "snapshot_identity"
            else source_identity(root)
        )
    )
    if identity != expected:
        raise projects.ProjectError(
            "shared source changed; restore and reconcile local edits"
        )


def restore(project_id: str, destination: Path) -> dict:
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise projects.ProjectError(
            "restore destination must not exist; preserve local edits"
        )
    reference = location(project_id) / "reference"
    manifest = json.loads((reference / "source.json").read_text())
    archive_path = reference / "source.zip"
    if digest(archive_path) != manifest["archive_sha256"]:
        raise projects.ProjectError("source archive checksum mismatch")
    # Validate the complete archive before writing any files.
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != set(manifest["files"]):
            raise projects.ProjectError("source archive manifest mismatch")
        for info in archive.infolist():
            name = info.filename
            if (
                "\\" in name
                or ":" in name
                or name.startswith("/")
                or any(p in ("", ".", "..") for p in name.split("/"))
                or (info.external_attr >> 16) & 0o170000 == 0o120000
            ):
                raise projects.ProjectError("unsafe source archive member")
            if (
                hashlib.sha256(archive.read(name)).hexdigest()
                != manifest["files"][name]
            ):
                raise projects.ProjectError("source member checksum mismatch")
        destination.mkdir(parents=True)
        for name in names:
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    projects.load_manifest(destination)
    _json(
        destination / ".publication-base.json",
        {
            "source_identity": manifest["source_identity"],
            **(
                {"snapshot_identity": manifest["snapshot_identity"]}
                if "snapshot_identity" in manifest
                else {}
            ),
        },
    )
    return {"project_id": project_id, "project": str(destination), "files": len(names)}


def generation_identity(root: Path) -> str:
    files = {
        p.relative_to(root).as_posix(): digest(p)
        for p in source_files(root)
        if p.relative_to(root).parts[0] != "verification"
        and p.suffix.lower() != ".md"
        and p.relative_to(root).as_posix() != "presentation.yaml"
    }
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def checkpoint_exports(root: Path, *, verified: bool = True) -> None:
    """Record a completed generator stage so proof-only fixes can resume safely."""
    folder = workspace.project_cache(root)
    _json(
        folder / "exports.json",
        {
            "identity": generation_identity(root),
            "verified": verified,
            "files": {
                p.relative_to(folder).as_posix(): digest(p)
                for p in (folder / "cad").rglob("*")
                if p.is_file()
            },
        },
    )


def rebuild(root: Path, *, verify: bool = True, reuse_exports: bool = False) -> dict:
    """Recreate declared outputs and project-specific review/proof scripts locally."""
    manifest = projects.load_manifest(root)
    log_path = workspace.project_cache(root) / "rebuild.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    commands = []
    if reuse_exports:
        state = json.loads((workspace.project_cache(root) / "exports.json").read_text())
        if verify and not state.get("verified", False):
            raise projects.ProjectError("export checkpoint was not verified")
        if state["identity"] != generation_identity(root):
            raise projects.ProjectError(
                "generator source changed; cannot reuse exports"
            )
        for name, checksum in state["files"].items():
            target = (workspace.project_cache(root) / name).resolve()
            if (
                not target.is_relative_to(workspace.project_cache(root))
                or not target.is_file()
                or digest(target) != checksum
            ):
                raise projects.ProjectError(
                    "export checkpoint changed; rebuild from source"
                )
    with log_path.open("a" if reuse_exports else "w", encoding="utf-8") as log:
        for declaration in [] if reuse_exports else manifest.generators:
            # Viewing-only meshes deliberately trade tessellation for browser size.
            # Actual individual-piece print packages and 2D exports get full verify.
            check = verify and (
                "3mf" in declaration.formats or declaration.kind == "2d"
            )
            args = [
                sys.executable,
                "-c",
                "from cad_context.cli import app; app()",
                "--quiet",
                "--project",
                str(root),
                "verify" if check else "generate",
                declaration.id,
            ]
            commands.append(declaration.id)
            result = subprocess.run(
                args,
                stdout=log,
                stderr=log,
                check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            log.flush()
            if result.returncode:
                raise projects.ProjectError(
                    f"rebuild failed: {declaration.id}; see {log_path}"
                )
            for fmt in declaration.formats:
                artifact = (
                    workspace.project_cache(root)
                    / "cad"
                    / declaration.id
                    / f"{declaration.id}.{fmt}"
                )
                if not artifact.is_file():
                    raise projects.ProjectError(f"missing rebuilt artifact: {artifact}")
            measurement = json.loads(
                (
                    workspace.project_cache(root)
                    / "cad"
                    / declaration.id
                    / f"{declaration.id}.measurements.json"
                ).read_text()
            )
            metrics = measurement["metrics"]
            if "volume_analytic" in metrics:
                reference = metrics["volume_analytic"]
                if abs(metrics["volume"] - reference) / reference > 0.01:
                    raise projects.ProjectError("native model/reference mismatch")
        if not reuse_exports:
            checkpoint_exports(root, verified=verify)
        else:
            commands.extend("reused:" + g.id for g in manifest.generators)
        for script in manifest.rebuild_scripts:
            target = (root / script).resolve()
            if not target.is_relative_to(root.resolve()):
                raise projects.ProjectError("rebuild script escapes source root")
            result = subprocess.run(
                [sys.executable, str(target)],
                stdout=log,
                stderr=log,
                check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            log.flush()
            if result.returncode:
                raise projects.ProjectError(f"rebuild failed: {script}; see {log_path}")
            commands.append(script)
    result = {
        "project_id": projects.identity(root),
        "verified": verify,
        "source_identity": source_identity(root),
        "commands": commands,
        "log": str(log_path),
        "artifacts": {
            p.relative_to(workspace.project_cache(root)).as_posix(): digest(p)
            for folder in ("cad", "evidence", "history", "exports")
            for p in (workspace.project_cache(root) / folder).rglob("*")
            if p.is_file()
        },
    }
    _json(workspace.project_cache(root) / "rebuild.json", result)
    return result


def _verified(root: Path) -> dict:
    path = workspace.project_cache(root) / "rebuild.json"
    if not path.exists():
        raise projects.ProjectError("run project rebuild before publishing")
    proof = json.loads(path.read_text())
    if not proof["verified"] or proof["source_identity"] != source_identity(root):
        raise projects.ProjectError(
            "source changed or build unverified; run project rebuild"
        )
    for name, checksum in proof.get("artifacts", {}).items():
        target = (workspace.project_cache(root) / name).resolve()
        if not target.is_relative_to(workspace.project_cache(root).resolve()):
            raise projects.ProjectError("invalid build artifact path")
        if not target.is_file() or digest(target) != checksum:
            raise projects.ProjectError("build artifacts changed; run project rebuild")
    return proof


def publish(project_id: str) -> dict:
    root = catalog.resolve(project_id)
    proof = _verified(root)
    _check_snapshot_base(root, location(project_id) / "reference")
    manifest = projects.load_manifest(root)
    parent = location(project_id) / "web"
    parent.mkdir(parents=True, exist_ok=True)
    stage, current, previous = (
        parent / n for n in (".latest-stage", "latest", ".latest-previous")
    )
    if stage.exists() or previous.exists():
        raise projects.ProjectError(
            "unfinished publication; inspect staging directories first"
        )
    stage.mkdir()
    models = []
    try:
        for name, generator in manifest.web_models.items():
            src = workspace.project_cache(root) / "cad" / generator / f"{generator}.glb"
            target = stage / f"{name}.glb"
            shutil.copy2(src, target)
            target.chmod(0o644)
            if digest(src) != digest(target):
                raise projects.ProjectError("publication copy mismatch")
            models.append(
                {
                    "id": name,
                    "file": target.name,
                    "sha256": digest(target),
                    "generator": generator,
                }
            )
        result = {
            "id": project_id,
            "name": manifest.name,
            "description": manifest.description,
            "source_identity": proof["source_identity"],
            "models": models,
            "physical_fit_tested": False,
        }
        references = []
        for name in manifest.web_files:
            candidate = workspace.project_cache(root) / name
            src = candidate if candidate.is_file() else root / name
            src = src.resolve()
            if not (
                src.is_relative_to(root.resolve())
                or src.is_relative_to(workspace.project_cache(root).resolve())
            ):
                raise projects.ProjectError("web reference escapes project")
            target = stage / Path(name).name
            if target.exists():
                raise projects.ProjectError("duplicate published file name")
            shutil.copy2(src, target)
            target.chmod(0o644)
            references.append({"file": target.name, "sha256": digest(target)})
        result["references"] = references
        _json(stage / "manifest.json", result)
        if current.exists():
            current.rename(previous)
        try:
            stage.rename(current)
        except Exception:
            if previous.exists():
                previous.rename(current)
            raise
        if previous.exists():
            _remove_publication_tree(previous, parent)
        snapshot(project_id)
        return result
    finally:
        if stage.exists():
            _remove_publication_tree(stage, parent)


def release(project_id: str, label: str, *, freeze: bool = False) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:-[a-z0-9-]+)?", label):
        raise projects.ProjectError(
            "release name must be YYYY-MM-DD with optional slug"
        )
    _valid_date(label)
    root = catalog.resolve(project_id)
    proof = _verified(root)
    manifest = projects.load_manifest(root)
    target = location(project_id) / "3d-print" / label
    if target.exists():
        raise projects.ProjectError(
            "release already exists; never overwrite a dated package"
        )
    # Stage all copies before making the release visible.
    stage = target.with_name("." + label + "-stage")
    if stage.exists():
        raise projects.ProjectError("unfinished release staging exists")
    stage.mkdir(parents=True)
    try:
        files = {}
        for name, generator in manifest.print_models.items():
            src = workspace.project_cache(root) / "cad" / generator / f"{generator}.3mf"
            shutil.copy2(src, stage / f"{name}.3mf")
            files[f"{name}.3mf"] = digest(stage / f"{name}.3mf")
        result = {
            "project_id": project_id,
            "release": label,
            "status": "frozen" if freeze else "draft",
            "files": files,
            "source_identity": proof["source_identity"],
            "physical_fit_tested": False,
            "generators": {
                f"{name}.3mf": generator
                for name, generator in manifest.print_models.items()
            },
        }
        _json(stage / "release.json", result)
        stage.rename(target)
        return result
    finally:
        if stage.exists():
            _remove_publication_tree(stage, target.parent)


def freeze(project_id: str, label: str) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:-[a-z0-9-]+)?", label):
        raise projects.ProjectError("invalid dated release name")
    _valid_date(label)
    path = location(project_id) / "3d-print" / label / "release.json"
    manifest = json.loads(path.read_text())
    for name, checksum in manifest["files"].items():
        if Path(name).name != name or digest(path.parent / name) != checksum:
            raise projects.ProjectError("release file checksum mismatch")
    manifest["status"] = "frozen"
    _json(path, manifest)
    return manifest


def _valid_date(label: str) -> None:
    try:
        date.fromisoformat(label[:10])
    except ValueError as exc:
        raise projects.ProjectError("invalid release date") from exc


def view(project_id: str) -> dict:
    root = location(project_id)
    path = root / "web/latest/manifest.json"
    published = json.loads(path.read_text()) if path.exists() else None
    gallery = root / "web/gallery/latest/manifest.json"
    presentation = (
        json.loads(gallery.read_text(encoding="utf-8")) if gallery.exists() else None
    )
    releases = []
    for p in sorted((root / "3d-print").glob("*/release.json"), reverse=True):
        release_data = json.loads(p.read_text())
        release_source = release_data.get("source_identity")
        published_source = published.get("source_identity") if published else None
        if not release_source:
            relation = "legacy-untracked"
        elif not published_source:
            relation = "no-published-source"
        elif release_source == published_source:
            relation = "same-source"
        else:
            relation = "different-source"
        releases.append(
            {
                "date": p.parent.name,
                **release_data,
                "published_source_relation": relation,
            }
        )
    return {
        "id": project_id,
        "publication_root": str(root),
        "published": published,
        "presentation": presentation,
        "releases": releases,
    }
