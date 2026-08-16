"""Backend availability probing.

Uses :func:`importlib.util.find_spec` so a probe never pays the (seconds-long)
cost of importing an OCCT kernel. External binaries are resolved through
:mod:`cad_context.artifacts`.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Backend:
    name: str
    extra: str
    modules: tuple[str, ...]
    binary: str | None = None
    description: str = ""


BACKENDS: dict[str, Backend] = {
    "shapely": Backend(
        "shapely",
        "vector2d",
        ("shapely", "ezdxf", "drawsvg"),
        description="2D geometry ops with SVG/DXF export",
    ),
    "build123d": Backend(
        "build123d",
        "build123d",
        ("build123d",),
        description="B-rep via OCCT, builder/algebra API",
    ),
    "openscad": Backend(
        "openscad",
        "openscad",
        ("solid2",),
        binary="openscad",
        description="CSG via solidpython2 + the OpenSCAD binary",
    ),
    "trimesh": Backend(
        "trimesh",
        "mesh",
        ("trimesh",),
        description="mesh inspection, booleans and glTF/GLB export",
    ),
}


def module_present(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        return False


def missing_modules(name: str) -> list[str]:
    backend = BACKENDS[name]
    return [m for m in backend.modules if not module_present(m)]


def available(name: str) -> bool:
    """True when the backend's Python packages are importable.

    An external binary (OpenSCAD) is *not* required for availability: those
    backends degrade gracefully, emitting source-level output only.
    """
    return not missing_modules(name)


def version(module: str) -> str | None:
    try:
        return importlib.metadata.version(module)
    except Exception:  # noqa: BLE001 - version reporting must never break a probe
        try:
            return getattr(importlib.import_module(module), "__version__", None)
        except Exception:  # noqa: BLE001
            return None


def status() -> list[dict[str, Any]]:
    """One row per backend, for ``cadctx info``."""
    from . import artifacts

    rows: list[dict[str, Any]] = []
    for backend in BACKENDS.values():
        missing = missing_modules(backend.name)
        row: dict[str, Any] = {
            "backend": backend.name,
            "extra": backend.extra,
            "available": not missing,
            "missing_modules": missing,
            "versions": {m: version(m) for m in backend.modules if module_present(m)},
            "description": backend.description,
        }
        if backend.binary:
            resolved = artifacts.resolve_executable(backend.binary)
            row["binary"] = backend.binary
            row["binary_path"] = str(resolved) if resolved else None
            row["degraded"] = not missing and resolved is None
        rows.append(row)
    return rows
