"""Generator registry with lazy built-in and project module loading."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..params import ShapeParams, describe
from ..types import BuildResult
from .models import AirfoilParams, BracketParams, PlateParams, WingParams


@dataclass(frozen=True)
class GeneratorSpec:
    id: str
    title: str
    kind: str
    backend: str
    module: str
    params_model: type[ShapeParams] | None
    formats: tuple[str, ...]
    params_class: str = ""
    description: str = ""
    family: str = ""
    origin: str = "builtin"
    project_root: Path | None = None
    artifact_root: Path | None = None
    parameter_defaults: dict[str, Any] | None = None
    exposure: dict[str, Any] | None = None
    project_name: str | None = None

    def _module(self):
        if self.project_root is not None:
            from ..projects import import_project_module

            return import_project_module(self.project_root, self.module)
        return importlib.import_module(self.module)

    def parameter_model(self) -> type[ShapeParams]:
        model = self.params_model
        if model is None:
            model = getattr(self._module(), self.params_class, None)
        if not isinstance(model, type) or not issubclass(model, ShapeParams):
            raise TypeError(
                f"{self.id!r} parameter model {self.params_class!r} "
                "must inherit ShapeParams"
            )
        return model

    def parse(self, overrides: dict[str, Any] | None = None) -> ShapeParams:
        values = dict(self.parameter_defaults or {})
        values.update(overrides or {})
        return self.parameter_model()(**values)

    def build(self, params: ShapeParams | dict[str, Any] | None = None) -> BuildResult:
        if params is None or isinstance(params, dict):
            params = self.parse(params)
        result = self._module().build(params)
        if result.generator != self.id:
            raise ValueError(
                f"generator {self.id!r} returned BuildResult for {result.generator!r}"
            )
        if result.backend != self.backend or result.kind != self.kind:
            raise ValueError(
                f"generator {self.id!r} returned backend/kind "
                f"{result.backend!r}/{result.kind!r}, expected "
                f"{self.backend!r}/{self.kind!r}"
            )
        return result

    def schema(self) -> dict[str, Any]:
        from .. import workspace

        payload = describe(self.parameter_model(), generator=self.id)
        defaults = self.parse().model_dump()
        for parameter in payload["parameters"]:
            parameter["default"] = defaults[parameter["name"]]
        payload.update(
            {
                "title": self.title,
                "kind": self.kind,
                "backend": self.backend,
                "family": self.family,
                "formats": list(self.formats),
                "description": self.description,
                "origin": self.origin,
                "project": self.project_name,
                "artifact_root": str(
                    (self.artifact_root or workspace.cad_dir()).resolve()
                ),
                "exposure": self.exposure,
            }
        )
        return payload


BUILTIN_SPECS: tuple[GeneratorSpec, ...] = (
    GeneratorSpec(
        id="plate2d",
        title="Slotted plate (2D)",
        kind="2d",
        backend="shapely",
        module="cad_context.generators.plate2d",
        params_model=PlateParams,
        formats=("svg", "dxf"),
        description="Rounded plate with parametric slots and corner holes.",
        family="plate",
    ),
    GeneratorSpec(
        id="airfoil",
        title="NACA 4-digit profile (2D)",
        kind="2d",
        backend="shapely",
        module="cad_context.generators.airfoil2d",
        params_model=AirfoilParams,
        formats=("svg", "dxf", "json"),
        description=(
            "Parametric airfoil section; JSON carries plot coordinates and markers."
        ),
        family="airfoil",
    ),
    GeneratorSpec(
        id="bracket-build123d",
        title="Flanged bracket (build123d)",
        kind="3d",
        backend="build123d",
        module="cad_context.generators.bracket_build123d",
        params_model=BracketParams,
        formats=("step", "stl", "glb"),
        description="Reference L-bracket built with build123d.",
        family="bracket",
    ),
    GeneratorSpec(
        id="wing-build123d",
        title="Lofted wing section (build123d)",
        kind="3d",
        backend="build123d",
        module="cad_context.generators.wing_build123d",
        params_model=WingParams,
        formats=("step", "stl", "glb"),
        description="Airfoil sections lofted into a tapered, twisted, swept wing.",
        family="wing",
    ),
)


def specs() -> tuple[GeneratorSpec, ...]:
    from ..projects import project_specs

    project = project_specs()
    builtin_ids = {item.id for item in BUILTIN_SPECS}
    collisions = sorted(builtin_ids & {item.id for item in project})
    if collisions:
        raise ValueError(
            "project generator id collision with built-in generator(s): "
            + ", ".join(collisions)
        )
    return BUILTIN_SPECS + project


def registry() -> dict[str, GeneratorSpec]:
    return {spec.id: spec for spec in specs()}


def get(generator_id: str) -> GeneratorSpec:
    entries = registry()
    try:
        return entries[generator_id]
    except KeyError:
        known = ", ".join(entries)
        raise KeyError(f"unknown generator {generator_id!r}; known: {known}") from None


def ids() -> list[str]:
    return list(registry())


def family(name: str, *, kind: str | None = None) -> list[GeneratorSpec]:
    if name not in families():
        known = ", ".join(families())
        raise KeyError(f"unknown family {name!r}; known: {known}")
    return [
        spec
        for spec in specs()
        if spec.family == name and (kind is None or spec.kind == kind)
    ]


def families() -> list[str]:
    return sorted({spec.family for spec in specs() if spec.family})


__all__ = [
    "BUILTIN_SPECS",
    "GeneratorSpec",
    "families",
    "family",
    "get",
    "ids",
    "registry",
    "specs",
]
