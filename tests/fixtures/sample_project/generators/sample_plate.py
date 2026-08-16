from __future__ import annotations

from cad_context.params import ShapeParams, number
from cad_context.types import BuildResult


class ProjectPlateParams(ShapeParams):
    width: float = number(
        60.0,
        minimum=10.0,
        maximum=200.0,
        description="Plate width",
    )
    height: float = number(
        30.0,
        minimum=10.0,
        maximum=100.0,
        description="Plate height",
    )


def build(params: ProjectPlateParams) -> BuildResult:
    from shapely.geometry import box

    native = box(0.0, 0.0, params.width, params.height)
    area = params.width * params.height
    return BuildResult(
        generator="project-plate",
        backend="shapely",
        kind="2d",
        params=params.model_dump(),
        native=native,
        metrics={
            "area": area,
            "area_analytic": area,
            "bounds": list(native.bounds),
            "units": "mm",
        },
    )
