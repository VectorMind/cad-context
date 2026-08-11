"""Exchange-format boundary.

Backends never talk to each other through objects — only through the files
written here. This module is the *only* place in the package that writes
geometry, and it always writes to the fixed per-generator directory
``.cache/cad/<generator>/`` unless a caller passes an explicit destination.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from .. import workspace
from ..types import BackendUnavailable, BuildResult
from . import export2d, export3d

#: Formats that carry geometry, in the order they must be produced (GLB is
#: derived from STL, so STL comes first).
FORMAT_ORDER = ("svg", "dxf", "scad", "step", "stl", "glb")

FORMAT_KIND = {
    "svg": "2d",
    "dxf": "2d",
    "scad": "3d",
    "step": "3d",
    "stl": "3d",
    "glb": "3d",
}


def destination(generator_id: str, fmt: str, out_dir: Path | None = None) -> Path:
    """Fixed path for one artifact.

    Stable across runs on purpose: a browser tab or an external viewer keeps
    pointing at the same file while parameters are iterated.
    """
    directory = Path(out_dir) if out_dir else workspace.generator_dir(generator_id)
    return directory / f"{generator_id}.{fmt}"


def export(
    build_result: BuildResult,
    formats: list[str] | tuple[str, ...],
    *,
    out_dir: Path | None = None,
    measure: bool = True,
) -> dict[str, Any]:
    """Write ``formats`` for a built result.

    Returns ``{"files": {fmt: path}, "measurements": {...}, "skipped": {...}}``.
    A format whose backend prerequisite is missing is *skipped*, not fatal —
    the OpenSCAD binary being absent must never fail a run.
    """
    ordered = [f for f in FORMAT_ORDER if f in set(formats)]
    unknown = sorted(set(formats) - set(FORMAT_ORDER))
    if unknown:
        raise ValueError(f"unknown format(s): {', '.join(unknown)}")

    files: dict[str, Path] = {}
    skipped: dict[str, str] = {}
    measurements: dict[str, Any] = {}

    for fmt in ordered:
        path = destination(build_result.generator, fmt, out_dir)
        try:
            if fmt == "svg":
                export2d.write_svg(build_result.native, path)
            elif fmt == "dxf":
                export2d.write_dxf(build_result.native, path)
            elif fmt == "scad":
                export3d.write_scad(build_result, path)
            elif fmt == "step":
                export3d.write_step(build_result, path)
            elif fmt == "stl":
                export3d.write_stl(build_result, path)
            elif fmt == "glb":
                # GLB is derived from a mesh. When the caller did not ask for
                # the STL itself, tessellate into a temporary file so only the
                # requested artifact lands in the workspace.
                if "stl" in files:
                    export3d.write_glb(files["stl"], path)
                else:
                    with tempfile.TemporaryDirectory(prefix="cadctx-") as scratch:
                        intermediate = Path(scratch) / f"{build_result.generator}.stl"
                        export3d.write_stl(build_result, intermediate)
                        export3d.write_glb(intermediate, path)
        except (BackendUnavailable, RuntimeError) as exc:
            skipped[fmt] = str(exc)
            continue
        files[fmt] = path

    if measure:
        mesh_source = files.get("stl") or files.get("glb")
        if mesh_source:
            measurements["mesh"] = export3d.mesh_metrics(mesh_source)
        if "dxf" in files:
            measurements["dxf"] = export2d.read_dxf_metrics(files["dxf"])
        if "svg" in files:
            measurements["svg"] = export2d.read_svg_metrics(files["svg"])

    return {"files": files, "skipped": skipped, "measurements": measurements}


__all__ = [
    "FORMAT_KIND",
    "FORMAT_ORDER",
    "destination",
    "export",
    "export2d",
    "export3d",
]
