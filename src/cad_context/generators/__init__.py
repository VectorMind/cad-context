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
from .models import AirfoilParams, BracketParams, PlateParams, WingParams


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
    #: Generators that build the *same* part on different backends share a
    #: family. It is what makes a cross-backend comparison meaningful: only
    #: generators of one family may be compared against one analytic reference.
    family: str = ""

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
                "family": self.family,
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
            "Parametric airfoil section; the JSON artifact carries the plot "
            "coordinates, camber line and thickness marker."
        ),
        family="airfoil",
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
        family="bracket",
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
        family="bracket",
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
    GeneratorSpec(
        id="wing-cadquery",
        title="Lofted wing section (CadQuery)",
        kind="3d",
        backend="cadquery",
        module="cad_context.generators.wing_cadquery",
        params_model=WingParams,
        formats=("step", "stl", "glb"),
        description="The same wing loft through CadQuery — switchable in the app.",
        family="wing",
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


def family(name: str, *, kind: str | None = None) -> list[GeneratorSpec]:
    """Every generator that builds the same part, optionally of one kind."""
    if name not in families():
        known = ", ".join(families())
        raise KeyError(f"unknown family {name!r}; known: {known}")
    return [
        spec
        for spec in SPECS
        if spec.family == name and (kind is None or spec.kind == kind)
    ]


def families() -> list[str]:
    return sorted({spec.family for spec in SPECS if spec.family})


__all__ = [
    "REGISTRY",
    "SPECS",
    "GeneratorSpec",
    "families",
    "family",
    "get",
    "ids",
]
