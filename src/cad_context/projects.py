"""External model-project discovery, manifests, and active-project state.

A project is trusted local code plus a small, versioned manifest.  Discovery is
cheap and does not import the project's Python modules; schema/build operations
load those modules lazily under a project-specific namespace.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
import types
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from . import workspace

PROJECT_ENV_VAR = "CAD_CONTEXT_PROJECT"
NO_PROJECT_ENV_VAR = "CAD_CONTEXT_NO_PROJECT"
POINTER_FILENAME = "active-project.json"
MANIFEST_FILENAME = "project.yaml"
GENERATOR_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
MODULE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")

_command_project: Path | None = None
_command_project_disabled = False


class ProjectError(RuntimeError):
    """A project path or manifest violates the public project contract."""


class Exposure(BaseModel):
    model_config = ConfigDict(extra="forbid")

    editable: list[str] = Field(default_factory=list)
    preview: str | None = None


class GeneratorDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    kind: Literal["2d", "3d"]
    backend: Literal["shapely", "build123d", "openscad"]
    module: str
    params_model: str
    formats: list[str]
    description: str = ""
    family: str = ""
    defaults: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        if not GENERATOR_ID_PATTERN.fullmatch(value):
            raise ValueError(
                "must be a lowercase slug (letters, digits, and single hyphens)"
            )
        return value

    @field_validator("module")
    @classmethod
    def valid_module(cls, value: str) -> str:
        if not MODULE_PATTERN.fullmatch(value):
            raise ValueError("must be a dotted module path inside the project")
        return value

    @field_validator("params_model")
    @classmethod
    def valid_params_model(cls, value: str) -> str:
        if not value.isidentifier():
            raise ValueError("must be a Python class name")
        return value

    @field_validator("formats")
    @classmethod
    def formats_are_unique(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("must declare at least one format")
        if len(value) != len(set(value)):
            raise ValueError("contains duplicate formats")
        return value


class ProjectManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = 1
    name: str
    description: str = ""
    generators: list[GeneratorDeclaration] = Field(default_factory=list)
    exposure: dict[str, Exposure] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value.strip()

    @model_validator(mode="after")
    def consistent_generator_references(self) -> ProjectManifest:
        ids = [generator.id for generator in self.generators]
        duplicates = sorted({item for item in ids if ids.count(item) > 1})
        if duplicates:
            raise ValueError(f"duplicate generator ids: {', '.join(duplicates)}")
        unknown = sorted(set(self.exposure) - set(ids))
        if unknown:
            raise ValueError(
                "exposure references unknown generator(s): " + ", ".join(unknown)
            )
        for generator_id, exposure in self.exposure.items():
            declaration = next(g for g in self.generators if g.id == generator_id)
            if exposure.preview and exposure.preview not in declaration.formats:
                raise ValueError(
                    f"exposure preview {exposure.preview!r} is not declared by "
                    f"{generator_id}"
                )
        return self


def configure_command_project(path: Path | None, *, disabled: bool = False) -> None:
    """Apply one CLI invocation's explicit project selection."""
    global _command_project, _command_project_disabled
    _command_project = path.expanduser().resolve() if path is not None else None
    _command_project_disabled = disabled


def pointer_path() -> Path:
    return workspace.cache_dir() / POINTER_FILENAME


def _pointer_project() -> Path | None:
    path = pointer_path()
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        value = payload["project"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ProjectError(f"invalid persisted project pointer at {path}") from exc
    return Path(value).expanduser().resolve()


def active_path(*, require_manifest: bool = True) -> Path | None:
    """Resolve ``--project`` > environment > persisted pointer > repository mode."""
    if _command_project_disabled:
        return None
    path = _command_project
    if path is None:
        if os.environ.get(NO_PROJECT_ENV_VAR) == "1":
            return None
        env = os.environ.get(PROJECT_ENV_VAR)
        path = Path(env).expanduser().resolve() if env else _pointer_project()
    if path is None:
        return None
    if not path.is_dir():
        raise ProjectError(f"project folder does not exist: {path}")
    if require_manifest and not (path / MANIFEST_FILENAME).is_file():
        raise ProjectError(
            f"project folder has no {MANIFEST_FILENAME}: {path}; "
            f"run `cadctx project init {path}` first"
        )
    return path


def persist(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    load_manifest(resolved)
    target = pointer_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"project": str(resolved)}, indent=2), encoding="utf-8"
    )
    temporary.replace(target)
    return resolved


def clear() -> bool:
    path = pointer_path()
    if not path.exists():
        return False
    path.unlink()
    return True


def manifest_path(path: Path | None = None) -> Path:
    root = path.expanduser().resolve() if path else active_path()
    if root is None:
        raise ProjectError("no active project")
    return root / MANIFEST_FILENAME


def load_manifest(path: Path | None = None) -> ProjectManifest:
    target = manifest_path(path)
    if not target.is_file():
        raise ProjectError(f"project manifest does not exist: {target}")
    try:
        raw = yaml.safe_load(target.read_text(encoding="utf-8"))
        return ProjectManifest.model_validate(raw)
    except (OSError, yaml.YAMLError, ValueError) as exc:
        raise ProjectError(f"invalid project manifest {target}: {exc}") from exc


def initialise(path: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Scaffold a project without overwriting existing files."""
    root = path.expanduser().resolve()
    manifest = root / MANIFEST_FILENAME
    if manifest.exists():
        raise ProjectError(f"refusing to overwrite existing manifest: {manifest}")
    directories = [root / "cad", root / "generators", root / "evidence"]
    payload = {
        "version": 1,
        "name": root.name,
        "description": "",
        "generators": [],
        "exposure": {},
    }
    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        manifest.write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
    return {
        "project": str(root),
        "manifest": str(manifest),
        "directories": [str(directory) for directory in directories],
        "dry_run": dry_run,
    }


def describe(path: Path | None = None) -> dict[str, Any]:
    root = path.expanduser().resolve() if path else active_path()
    if root is None:
        return {"active": False, "project": None, "manifest": None}
    manifest = load_manifest(root)
    return {
        "active": True,
        "project": str(root),
        "manifest": str(root / MANIFEST_FILENAME),
        "name": manifest.name,
        "description": manifest.description,
        "generator_ids": [generator.id for generator in manifest.generators],
        "cad": str((root / "cad").resolve()),
    }


def _namespace(root: Path) -> str:
    digest = sha256(str(root).encode()).hexdigest()[:12]
    return f"_cadctx_project_{digest}"


@contextmanager
def _without_bytecode():
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        yield
    finally:
        sys.dont_write_bytecode = previous


def import_project_module(root: Path, module: str):
    """Import one project module under a collision-proof namespace."""
    namespace = _namespace(root)
    if namespace not in sys.modules:
        package = types.ModuleType(namespace)
        package.__path__ = [str(root)]  # type: ignore[attr-defined]
        package.__package__ = namespace
        sys.modules[namespace] = package
    full_name = f"{namespace}.{module}"
    try:
        with _without_bytecode():
            return importlib.import_module(full_name)
    except Exception as exc:
        raise ProjectError(
            f"failed to import project module {module!r} from {root}: {exc}"
        ) from exc


def project_specs() -> tuple[Any, ...]:
    """Create lazy GeneratorSpec values from the active manifest."""
    root = active_path()
    if root is None:
        return ()
    manifest = load_manifest(root)
    from .generators import GeneratorSpec

    specs = []
    for declaration in manifest.generators:
        exposure = manifest.exposure.get(declaration.id, Exposure())
        specs.append(
            GeneratorSpec(
                id=declaration.id,
                title=declaration.title,
                kind=declaration.kind,
                backend=declaration.backend,
                module=declaration.module,
                params_model=None,
                params_class=declaration.params_model,
                formats=tuple(declaration.formats),
                description=declaration.description,
                family=declaration.family or declaration.id,
                origin="project",
                project_root=root,
                artifact_root=(root / "cad").resolve(),
                parameter_defaults=declaration.defaults,
                exposure={
                    "editable": exposure.editable,
                    "preview": exposure.preview,
                },
                project_name=manifest.name,
            )
        )
    return tuple(specs)


__all__ = [
    "GENERATOR_ID_PATTERN",
    "MANIFEST_FILENAME",
    "NO_PROJECT_ENV_VAR",
    "PROJECT_ENV_VAR",
    "ProjectError",
    "ProjectManifest",
    "active_path",
    "clear",
    "configure_command_project",
    "describe",
    "import_project_module",
    "initialise",
    "load_manifest",
    "persist",
    "pointer_path",
    "project_specs",
]
