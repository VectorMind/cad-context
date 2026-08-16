from __future__ import annotations

from cad_context.params import ShapeParams, number
from cad_context.types import BuildResult


class OpenScadBoxParams(ShapeParams):
    width: float = number(
        20.0,
        minimum=5.0,
        maximum=100.0,
        description="Box width",
    )
    depth: float = number(
        15.0,
        minimum=5.0,
        maximum=100.0,
        description="Box depth",
    )
    height: float = number(
        10.0,
        minimum=5.0,
        maximum=100.0,
        description="Box height",
    )


def build(params: OpenScadBoxParams) -> BuildResult:
    from solid2 import cube

    volume = params.width * params.depth * params.height
    return BuildResult(
        generator="project-openscad-box",
        backend="openscad",
        kind="3d",
        params=params.model_dump(),
        native=cube([params.width, params.depth, params.height]),
        metrics={"volume_analytic": volume, "units": "mm"},
    )
