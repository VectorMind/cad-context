"""2D exchange formats: SVG (drawsvg) and DXF (ezdxf).

Contract: millimetre units, Y up, origin at the part's own frame origin.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

STROKE_WIDTH = 0.4
MARGIN = 5.0

#: DXF $INSUNITS codes we care about (the contract is millimetres).
_UNIT_NAMES = {0: "unitless", 1: "in", 4: "mm", 5: "cm", 6: "m"}


def _rings(
    geometry: Any,
) -> tuple[list[list[tuple[float, float]]], list[list[tuple[float, float]]]]:
    """Split a Polygon/MultiPolygon into exterior and interior rings."""
    exteriors: list[list[tuple[float, float]]] = []
    interiors: list[list[tuple[float, float]]] = []
    polygons = getattr(geometry, "geoms", None) or [geometry]
    for polygon in polygons:
        exteriors.append([(float(x), float(y)) for x, y in polygon.exterior.coords])
        for ring in polygon.interiors:
            interiors.append([(float(x), float(y)) for x, y in ring.coords])
    return exteriors, interiors


def write_svg(geometry: Any, path: Path) -> Path:
    import drawsvg

    minx, miny, maxx, maxy = geometry.bounds
    width = (maxx - minx) + 2 * MARGIN
    height = (maxy - miny) + 2 * MARGIN
    drawing = drawsvg.Drawing(
        width, height, origin=(minx - MARGIN, miny - MARGIN), id_prefix="cadctx"
    )
    exteriors, interiors = _rings(geometry)
    commands: list[str] = []
    for ring in exteriors + interiors:
        head, *tail = ring
        commands.append(
            "M {:.6f} {:.6f} ".format(*head)
            + " ".join(f"L {x:.6f} {y:.6f}" for x, y in tail)
            + " Z"
        )
    drawing.append(
        drawsvg.Path(
            d=" ".join(commands),
            fill="#b8c4d0",
            fill_rule="evenodd",
            stroke="#1f2933",
            stroke_width=STROKE_WIDTH,
        )
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    drawing.set_pixel_scale(2)
    drawing.save_svg(str(path))
    return path


def write_dxf(geometry: Any, path: Path) -> Path:
    import ezdxf

    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    msp = doc.modelspace()
    exteriors, interiors = _rings(geometry)
    doc.layers.add("OUTLINE", color=7)
    doc.layers.add("CUTOUTS", color=1)
    for ring in exteriors:
        msp.add_lwpolyline(ring[:-1], close=True, dxfattribs={"layer": "OUTLINE"})
    for ring in interiors:
        msp.add_lwpolyline(ring[:-1], close=True, dxfattribs={"layer": "CUTOUTS"})
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(path))
    return path


def read_dxf_metrics(path: Path) -> dict[str, Any]:
    """Round-trip check for a written DXF: reload and measure."""
    import ezdxf

    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    polylines = list(msp.query("LWPOLYLINE"))
    points = [p for pl in polylines for p in pl.get_points("xy")]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return {
        "polylines": len(polylines),
        "vertices": len(points),
        "bounds": [min(xs), min(ys), max(xs), max(ys)] if points else [],
        "units": int(doc.units),
        "units_name": _UNIT_NAMES.get(int(doc.units), "unknown"),
    }


def read_svg_metrics(path: Path) -> dict[str, Any]:
    """Cheap structural check for a written SVG (no rasteriser needed)."""
    text = path.read_text(encoding="utf-8")
    return {
        "bytes": len(text),
        "paths": text.count("<path"),
        "has_viewbox": "viewBox" in text,
    }
