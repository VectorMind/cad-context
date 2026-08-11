"""Generator registry.

Every generator is declared here with its parameter model and its formats.
Builder modules are imported lazily so that listing generators, printing a
parameter schema, or probing the environment never pays an OCCT import.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from ..params import ShapeParams, describe
from ..types import BuildResult
from .models import BracketParams, PlateParams


@dataclass(frozen=True)
class GeneratorSpec:
    id: str
    title: str
    kind: str  # "2d" | "3d"
    backend: str
    module: str
    params_model: type[ShapeParams]
    formats: tuple[str, ...]
    description: str = ""

    def parse(self, overrides: dict[str, Any] | None = None) -> ShapeParams:
        return self.params_model(**(overrides or {}))

    def build(self, params: ShapeParams | dict[str, Any] | None = None) -> BuildResult:
        if params is None or isinstance(params, dict):
            params = self.parse(params)
        module = importlib.import_module(self.module)
        return module.build(params)

    def schema(self) -> dict[str, Any]:
        payload = describe(self.params_model, generator=self.id)
        payload.update(
            {
                "title": self.title,
                "kind": self.kind,
                "backend": self.backend,
                "formats": list(self.formats),
                "description": self.description,
            }
        )
        return payload


SPECS: tuple[GeneratorSpec, ...] = (
    GeneratorSpec(
        id="plate2d",
        title="Slotted plate (2D)",
        kind="2d",
        backend="shapely",
        module="cad_context.generators.plate2d",
        params_model=PlateParams,
        formats=("svg", "dxf"),
        description="Rounded plate with parametric slots and corner holes.",
    ),
    GeneratorSpec(
        id="bracket-cadquery",
        title="Flanged bracket (CadQuery)",
        kind="3d",
        backend="cadquery",
        module="cad_context.generators.bracket_cadquery",
        params_model=BracketParams,
        formats=("step", "stl", "glb"),
        description="Reference L-bracket built with CadQuery's OCCT kernel.",
    ),
    GeneratorSpec(
        id="bracket-build123d",
        title="Flanged bracket (build123d)",
        kind="3d",
        backend="build123d",
        module="cad_context.generators.bracket_build123d",
        params_model=BracketParams,
        formats=("step", "stl", "glb"),
        description="The same reference L-bracket in build123d's algebra API.",
    ),
    GeneratorSpec(
        id="bracket-openscad",
        title="Flanged bracket (OpenSCAD)",
        kind="3d",
        backend="openscad",
        module="cad_context.generators.bracket_openscad",
        params_model=BracketParams,
        formats=("scad", "stl", "glb"),
        description="The same reference L-bracket as CSG; STL needs the binary.",
    ),
)

REGISTRY: dict[str, GeneratorSpec] = {spec.id: spec for spec in SPECS}


def get(generator_id: str) -> GeneratorSpec:
    try:
        return REGISTRY[generator_id]
    except KeyError:
        known = ", ".join(REGISTRY)
        raise KeyError(f"unknown generator {generator_id!r}; known: {known}") from None


def ids() -> list[str]:
    return list(REGISTRY)


__all__ = ["REGISTRY", "SPECS", "GeneratorSpec", "get", "ids"]
