"""Exchange-format boundary.

Backends never talk to each other through objects — only through the files
written here. This module is the *only* place in the package that writes
geometry, and it always writes to the fixed per-generator directory
``.cache/cad/<generator>/`` unless a caller passes an explicit destination.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

from .. import workspace
from ..types import BackendUnavailable, BuildResult
from . import export2d, export3d

#: Formats that carry geometry, in the order they must be produced (GLB is
#: derived from STL, so STL comes first).
FORMAT_ORDER = ("svg", "dxf", "json", "scad", "step", "stl", "glb")

FORMAT_KIND = {
    "svg": "2d",
    "dxf": "2d",
    "json": "2d",
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

    def write_atomic(path: Path, writer) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(
            f".{path.stem}.tmp-{uuid.uuid4().hex[:8]}{path.suffix}"
        )
        try:
            writer(temporary)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    for fmt in ordered:
        path = destination(build_result.generator, fmt, out_dir)
        try:
            if fmt == "svg":
                write_atomic(
                    path,
                    lambda target: export2d.write_svg(build_result.native, target),
                )
            elif fmt == "dxf":
                write_atomic(
                    path,
                    lambda target: export2d.write_dxf(build_result.native, target),
                )
            elif fmt == "json":
                if build_result.payload is None:
                    # A generator that declares the format must publish one:
                    # this is a wiring bug, not a missing prerequisite.
                    raise ValueError(
                        f"{build_result.generator!r} declares the json format "
                        "but published no payload"
                    )
                write_atomic(
                    path,
                    lambda target: export2d.write_json(build_result.payload, target),
                )
            elif fmt == "scad":
                write_atomic(
                    path, lambda target: export3d.write_scad(build_result, target)
                )
            elif fmt == "step":
                write_atomic(
                    path, lambda target: export3d.write_step(build_result, target)
                )
            elif fmt == "stl":
                write_atomic(
                    path, lambda target: export3d.write_stl(build_result, target)
                )
            elif fmt == "glb":
                # GLB is derived from a mesh. When the caller did not ask for
                # the STL itself, tessellate into a temporary file so only the
                # requested artifact lands in the workspace.
                if "stl" in files:
                    write_atomic(
                        path,
                        lambda target: export3d.write_glb(files["stl"], target),
                    )
                else:
                    with tempfile.TemporaryDirectory(prefix="cadctx-") as scratch:
                        intermediate = Path(scratch) / f"{build_result.generator}.stl"
                        export3d.write_stl(build_result, intermediate)
                        write_atomic(
                            path,
                            lambda target, source=intermediate: export3d.write_glb(
                                source, target
                            ),
                        )
        except (BackendUnavailable, RuntimeError) as exc:
            skipped[fmt] = str(exc)
            continue
        files[fmt] = path

    if measure:
        mesh_source = files.get("stl") or files.get("glb")
        if mesh_source:
            measurements["mesh"] = export3d.mesh_metrics(mesh_source)
        if "step" in files:
            measurements["step"] = export3d.read_step_metrics(files["step"])
        if "dxf" in files:
            measurements["dxf"] = export2d.read_dxf_metrics(files["dxf"])
        if "svg" in files:
            measurements["svg"] = export2d.read_svg_metrics(files["svg"])
        if "json" in files:
            measurements["json"] = export2d.read_json_metrics(files["json"])

    measurement_file: Path | None = None
    if measure:
        from .. import generators

        spec = generators.get(build_result.generator)
        if spec.origin == "project":
            directory = Path(out_dir) if out_dir else workspace.generator_dir(spec.id)
            measurement_file = directory / f"{spec.id}.measurements.json"
            summary = {
                "generator": spec.id,
                "params": build_result.params,
                "metrics": build_result.metrics,
                "files": {fmt: str(path) for fmt, path in files.items()},
                "measurements": measurements,
                "skipped": skipped,
            }
            write_atomic(
                measurement_file,
                lambda target: target.write_text(
                    json.dumps(summary, indent=2), encoding="utf-8"
                ),
            )

    return {
        "files": files,
        "skipped": skipped,
        "measurements": measurements,
        "measurement_file": measurement_file,
    }


__all__ = [
    "FORMAT_KIND",
    "FORMAT_ORDER",
    "destination",
    "export",
    "export2d",
    "export3d",
]
