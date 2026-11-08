"""Publish project visual history without rebuilding or changing model releases."""

from __future__ import annotations

import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from . import project_catalog, projects, publication, workspace

DEFINITION = "presentation.yaml"
IMAGE_TYPES = {".svg", ".png", ".jpg", ".jpeg", ".webp"}
State = Literal["reference", "history", "approved", "review"]


class Visual(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    location: Literal["source", "cache"] = "source"
    title: str
    caption: str = ""
    state: State | None = None
    wide: bool = False

    @field_validator("path")
    @classmethod
    def valid_image_path(cls, value: str) -> str:
        projects.PortfolioDeclaration.safe_path(value)
        if Path(value).suffix.lower() not in IMAGE_TYPES:
            raise ValueError("visual history accepts image files only")
        return value


class Stage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str = ""
    state: State = "history"
    assets: list[Visual] = Field(min_length=1)

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        if not projects.GENERATOR_ID_PATTERN.fullmatch(value):
            raise ValueError("stage ID must be a lowercase slug")
        return value


class Presentation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1] = 1
    title: str
    description: str = ""
    stages: list[Stage] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_paths(self):
        ids = [stage.id for stage in self.stages]
        if len(ids) != len(set(ids)):
            raise ValueError("stage IDs must be unique")
        for stage in self.stages:
            names = [Path(asset.path).name for asset in stage.assets]
            if len(names) != len(set(names)):
                raise ValueError("image filenames must be unique within a stage")
        return self


def load(root: Path) -> Presentation:
    return Presentation.model_validate(
        yaml.safe_load((root / DEFINITION).read_text(encoding="utf-8"))
    )


def _rename(source: Path, target: Path) -> None:
    # Drive/antivirus can hold newly copied nested directories briefly.
    for attempt in range(10):
        source.chmod(0o755)
        try:
            source.rename(target)
            return
        except PermissionError:
            if attempt == 9:
                raise
            time.sleep(0.5 * (attempt + 1))


def present(project_id: str) -> dict:
    """Copy declared visual stages only; preserve all existing geometry bytes."""
    root = project_catalog.resolve(project_id)
    definition = load(root)
    shared = publication.location(project_id)
    publication._check_snapshot_base(root, shared / "reference")
    # Preflight every dependency before changing the shared gallery.
    sources = []
    for stage in definition.stages:
        for asset in stage.assets:
            boundary = (
                root if asset.location == "source" else workspace.project_cache(root)
            ).resolve()
            source = (boundary / asset.path).resolve()
            if not source.is_relative_to(boundary):
                raise projects.ProjectError("visual asset escapes its declared root")
            if not source.is_file():
                raise projects.ProjectError(
                    f"missing visual asset: {asset.path}; rebuild project cache first"
                )
            if source.suffix.lower() == ".svg":
                if ET.parse(source).getroot().tag != "{http://www.w3.org/2000/svg}svg":
                    raise projects.ProjectError("visual SVG root is invalid")
            sources.append((stage, asset, source))
    parent = shared / "web/gallery"
    parent.mkdir(parents=True, exist_ok=True)
    stage_path = parent / ".latest-stage"
    previous = parent / ".latest-previous"
    current = parent / "latest"
    if stage_path.exists() or previous.exists():
        raise projects.ProjectError("unfinished visual publication; inspect staging")
    stage_path.mkdir()
    result = {
        "title": definition.title,
        "description": definition.description,
        "definition_sha256": publication.digest(root / DEFINITION),
        "source_identity": publication.source_identity(root),
        "asset_count": len(sources),
        "stages": [],
    }
    try:
        for stage in definition.stages:
            item = stage.model_dump(exclude={"assets"})
            item["assets"] = []
            for owner, asset, source in sources:
                if owner.id != stage.id:
                    continue
                name = f"{stage.id}/{source.name}"
                target = stage_path / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                target.chmod(0o644)
                if publication.digest(source) != publication.digest(target):
                    raise projects.ProjectError("visual publication copy mismatch")
                item["assets"].append(
                    {
                        **asset.model_dump(exclude={"path", "location"}),
                        "file": name,
                        "sha256": publication.digest(target),
                    }
                )
            result["stages"].append(item)
        publication._json(stage_path / "manifest.json", result)
        if current.exists():
            _rename(current, previous)
        try:
            _rename(stage_path, current)
        except Exception:
            if previous.exists():
                _rename(previous, current)
            raise
        if previous.exists():
            publication._remove_publication_tree(previous, parent)
        publication.snapshot(project_id)
        return {"project_id": project_id, **result}
    finally:
        if stage_path.exists():
            publication._remove_publication_tree(stage_path, parent)
