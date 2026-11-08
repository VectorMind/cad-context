"""Portable project names and machine-local storage roots; no code imports."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from . import workspace


class Root(BaseModel):
    model_config = ConfigDict(extra="forbid")
    env: str | None = None
    candidates: list[str] = Field(default_factory=list)


class Location(BaseModel):
    model_config = ConfigDict(extra="forbid")
    root: str
    path: str

    @field_validator("path")
    @classmethod
    def confined(cls, value: str) -> str:
        if any(p in ("", ".", "..") for p in value.split("/")) or any(
            c in value for c in "\\:"
        ):
            raise ValueError("project path must be a confined relative POSIX path")
        return value


class Entry(Location):
    publication: Location | None = None


class Catalog(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    default: str | None = None
    roots: dict[str, Root] = Field(default_factory=dict)
    projects: dict[str, Entry] = Field(default_factory=dict)

    @model_validator(mode="after")
    def references(self):
        if self.default is not None and self.default not in self.projects:
            raise ValueError("default must name a registered project")
        for name, entry in self.projects.items():
            if not name or any(c in name for c in "/\\:"):
                raise ValueError("project ids must be nonempty names, not paths")
            if entry.root not in self.roots:
                raise ValueError(f"unknown root {entry.root!r} for {name}")
            if entry.publication and entry.publication.root not in self.roots:
                raise ValueError(f"unknown publication root for {name}")
        return self


def catalog_path() -> Path:
    return workspace.repo_root() / "config" / "projects.yaml"


def local_path() -> Path:
    return catalog_path().with_name("projects.local.yaml")


def load() -> Catalog:
    from .projects import ProjectError

    path = catalog_path()
    if not path.exists():
        return Catalog()
    try:
        return Catalog.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise ProjectError(f"invalid project catalog {path}: {exc}") from exc


def local_roots() -> dict[str, str]:
    from .projects import ProjectError

    path = local_path()
    if not path.exists():
        return {}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or set(raw) != {"roots"}:
            raise ValueError("expected a roots mapping")
        roots = raw["roots"]
        if not isinstance(roots, dict) or not all(
            isinstance(k, str) and isinstance(v, str) and v for k, v in roots.items()
        ):
            raise ValueError("root names and paths must be strings")
        return roots
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise ProjectError(f"invalid local project roots {path}: {exc}") from exc


def resolve_root(name: str, catalog: Catalog) -> Path | None:
    declaration = catalog.roots[name]
    value = os.environ.get(declaration.env) if declaration.env else None
    value = value or local_roots().get(name)
    if value:
        return Path(value).expanduser().resolve()
    candidates = [Path(p).expanduser().resolve() for p in declaration.candidates]
    available = list(dict.fromkeys(p for p in candidates if p.is_dir()))
    if len(available) > 1:
        from .projects import ProjectError

        raise ProjectError(
            f"ambiguous root {name}; run cadcon project root {name} <path>"
        )
    return available[0] if available else None


def resolve(name: str, catalog: Catalog | None = None) -> Path:
    from .projects import ProjectError

    catalog = catalog or load()
    entry = catalog.projects[name]
    root = resolve_root(entry.root, catalog)
    if root is None:
        raise ProjectError(
            f"project {name}: root {entry.root} unavailable; "
            f"run cadcon project root {entry.root} <path>"
        )
    path = (root / entry.path).resolve()
    if not path.is_relative_to(root):
        raise ProjectError(f"project {name} escapes root {entry.root}")
    return path


def bind(name: str, path: Path) -> Path:
    from .projects import ProjectError

    if name not in load().roots:
        raise ProjectError(f"unknown catalog root: {name}")
    resolved = path.expanduser().resolve()
    if not resolved.is_dir():
        raise ProjectError(f"root folder does not exist: {resolved}")
    roots = local_roots()
    roots[name] = str(resolved)
    target = local_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(yaml.safe_dump({"roots": roots}), encoding="utf-8")
    temporary.replace(target)
    return resolved


def listing() -> dict:
    """List registered entries and immediate child manifests, without importing."""
    from .projects import MANIFEST_FILENAME, ProjectError, load_manifest

    catalog = load()
    rows = []
    known = set()
    for name in catalog.projects:
        entry = catalog.projects[name]
        published_available = False
        if entry.publication:
            try:
                parent = resolve_root(entry.publication.root, catalog)
                published_available = bool(
                    parent
                    and (
                        parent / entry.publication.path / "web/latest/manifest.json"
                    ).is_file()
                )
            except ProjectError:
                pass
        path = None
        error = None
        try:
            path = resolve(name, catalog)
            known.add(path)
            manifest = load_manifest(path)
            title = manifest.name
        except ProjectError as exc:
            error = str(exc)
            title = name
        rows.append(
            {
                "id": name,
                "name": title,
                "path": str(path) if path else None,
                "registered": True,
                "default": name == catalog.default,
                "available": error is None,
                "published_available": published_available,
                "error": error,
            }
        )
    roots = {}
    root_errors = {}
    for name in catalog.roots:
        try:
            root = resolve_root(name, catalog)
        except ProjectError as exc:
            roots[name] = None
            root_errors[name] = str(exc)
            continue
        roots[name] = str(root) if root else None
        if root is None or not root.is_dir():
            continue
        for child in sorted(root.iterdir()):
            path = child.resolve()
            if (
                not path.is_relative_to(root)
                or path in known
                or not (path / MANIFEST_FILENAME).is_file()
            ):
                continue
            try:
                raw = yaml.safe_load(
                    (path / MANIFEST_FILENAME).read_text(encoding="utf-8")
                )
                if not isinstance(raw, dict) or raw.get("tool") != "cadcon":
                    continue
                manifest = load_manifest(path)
                error = None
                title = manifest.name
            except (ProjectError, OSError, yaml.YAMLError):
                # Discovery includes only valid, explicitly identified projects.
                # Registered invalid entries remain visible above for diagnosis.
                continue
            known.add(path)
            rows.append(
                {
                    "id": None,
                    "name": title,
                    "path": str(path),
                    "registered": False,
                    "default": False,
                    "available": error is None,
                    "error": error,
                }
            )
    return {
        "default": catalog.default,
        "roots": roots,
        "root_errors": root_errors,
        "projects": rows,
    }
