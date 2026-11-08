"""3D exchange formats: STEP and STL per kernel, GLB through trimesh.

Contract: millimetre units, Z up, part frame as built. Every 3D backend path
ends in at least STL and GLB so the companion web app can render any of them
without knowing which kernel produced the geometry.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from ..types import BackendUnavailable

#: Tessellation quality for STL export, in millimetres / radians.
LINEAR_TOLERANCE = 0.01
ANGULAR_TOLERANCE = 0.1


def write_step(build_result: Any, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backend = build_result.backend
    if backend == "build123d":
        from build123d import export_step

        export_step(build_result.native, str(path))
    else:
        raise BackendUnavailable(f"backend {backend!r} cannot export STEP")
    return path


def write_stl(build_result: Any, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    backend = build_result.backend
    if backend == "build123d":
        from build123d import export_stl

        quality = build_result.tessellation
        if quality and quality.stl_writer == "mesher":
            try:
                from build123d import Mesher, Unit

                mesher = Mesher(unit=Unit.MM)
            except (ImportError, OSError) as exc:
                raise BackendUnavailable(
                    f"Mesher STL runtime unavailable: {exc}"
                ) from exc
            mesher.add_shape(
                build_result.native,
                linear_deflection=quality.linear_deflection,
                angular_deflection=quality.angular_deflection,
            )
            mesher.write(path)
            return path
        export_stl(
            build_result.native,
            str(path),
            tolerance=quality.linear_deflection if quality else LINEAR_TOLERANCE,
            angular_tolerance=(
                quality.angular_deflection if quality else ANGULAR_TOLERANCE
            ),
        )
    elif backend == "openscad":
        scad_path = path.with_suffix(".scad")
        try:
            write_scad(build_result, scad_path)
            render_scad(scad_path, path)
        finally:
            scad_path.unlink(missing_ok=True)
    else:
        raise BackendUnavailable(f"backend {backend!r} cannot export STL")
    return path


def write_scad(build_result: Any, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    source = build_result.native.as_scad()
    path.write_text(source + "\n", encoding="utf-8")
    return path


def openscad_executable() -> Path | None:
    from .. import artifacts

    return artifacts.resolve_executable("openscad")


def render_scad(scad_path: Path, out_path: Path) -> Path:
    """Render a ``.scad`` file with the OpenSCAD binary."""
    executable = openscad_executable()
    if executable is None:
        raise BackendUnavailable(
            "OpenSCAD binary not found — run `cadcon fetch openscad` "
            "or put `openscad` on PATH"
        )
    command = [str(executable), "-o", str(out_path), str(scad_path)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=600)
    if completed.returncode != 0 or not out_path.exists():
        raise RuntimeError(
            f"openscad failed (exit {completed.returncode}): "
            f"{completed.stderr.strip()[:400]}"
        )
    return out_path


def write_glb(stl_path: Path, path: Path) -> Path:
    """Convert an existing mesh file to GLB — the web-app bridge format."""
    import trimesh

    mesh = trimesh.load_mesh(str(stl_path))
    path.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(str(path))
    return path


def colored_parts(build_result: Any) -> list[tuple[Any, Any]]:
    """Read optional native assembly colours only inside the exporter boundary."""
    if build_result.backend != "build123d":
        return []
    parts = []

    def visit(shape, inherited=None):
        color = getattr(shape, "color", None) or inherited
        children = getattr(shape, "children", ())
        if children:
            for child in children:
                visit(child, color)
        else:
            parts.append((shape.located(shape.global_location), color))

    visit(build_result.native)
    return parts if any(color is not None for _, color in parts) else []


def write_colored_glb(build_result: Any, path: Path) -> Path:
    """Tessellate native parts separately so GLB retains solid PBR colours."""
    import tempfile
    from dataclasses import replace

    import numpy as np
    import trimesh

    scene = trimesh.Scene()
    with tempfile.TemporaryDirectory(prefix="cadcon-colors-") as temporary:
        for index, (shape, color) in enumerate(colored_parts(build_result)):
            source = Path(temporary) / f"part-{index}.stl"
            write_stl(replace(build_result, native=shape), source)
            mesh = trimesh.load_mesh(str(source))
            rgba = tuple(color) if color is not None else (0.72, 0.77, 0.82, 1)
            # Native preview palette is sRGB; glTF base colour factors are linear.
            linear = [
                c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                for c in rgba[:3]
            ]
            factor = np.rint(np.array([*linear, rgba[3]]) * 255).astype(np.uint8)
            name = getattr(shape, "label", "") or f"part-{index}"
            material = trimesh.visual.material.PBRMaterial(
                name=f"cadcon:{name}",
                baseColorFactor=factor,
                metallicFactor=0.0,
                roughnessFactor=0.9,
                alphaMode="OPAQUE",
            )
            mesh.visual = trimesh.visual.TextureVisuals(material=material)
            scene.add_geometry(mesh, geom_name=name, node_name=name)
    scene.export(str(path), file_type="glb")
    return path


def mesh_metrics(mesh_path: Path) -> dict[str, Any]:
    """Load a mesh back and measure it — the proof that an export is real."""
    import trimesh

    mesh = trimesh.load_mesh(str(mesh_path))
    bounds = mesh.bounds
    return {
        "volume": float(abs(mesh.volume)),
        "area": float(mesh.area),
        "watertight": bool(mesh.is_watertight),
        "vertices": int(len(mesh.vertices)),
        "faces": int(len(mesh.faces)),
        "bounds_min": [float(v) for v in bounds[0]],
        "bounds_max": [float(v) for v in bounds[1]],
    }


def read_step_metrics(step_path: Path) -> dict[str, Any]:
    """Round-trip a STEP file back through a kernel and measure the solid."""
    try:
        from build123d import import_step

        shape = import_step(str(step_path))
        bbox = shape.bounding_box()
        return {
            "volume": float(shape.volume),
            "area": float(shape.area),
            "bounds_min": [float(value) for value in bbox.min],
            "bounds_max": [float(value) for value in bbox.max],
        }
    except ImportError as exc:  # pragma: no cover - depends on installed extras
        raise BackendUnavailable("STEP round-trip needs the build123d extra") from exc
