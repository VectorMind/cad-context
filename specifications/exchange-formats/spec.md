# Exchange Formats And Verification

## Boundary

Shared behavior crosses backend boundaries only through files. No module outside
a generator or exporter interprets a backend-native object. Units are
millimetres; 3D is Z-up; 2D is Y-up on the generator's declared datum.

| Generator path | Required outputs | Additional output |
| --- | --- | --- |
| 2D Shapely | SVG and DXF | JSON coordinate payload when useful |
| 3D build123d B-rep | STL and GLB | STEP |
| Optional OpenSCAD project | SCAD source | STL and GLB when its binary resolves |

GLB is derived from STL through trimesh. STEP is the lossless B-rep interchange
format. A missing external OpenSCAD binary degrades to SCAD-only output and
records every skipped format; it does not crash generation.

## Tessellation

build123d meshes use 0.01 mm linear and 0.1 rad angular tolerance. OpenSCAD
project generators choose enough facets to remain inside the 1% mesh agreement
budget.

## Round-Trip Measurements

Every generated format is re-read when measurement is enabled:

- STL/GLB: volume, area, watertightness, bounds, vertices, and faces;
- STEP: build123d re-import, volume, area, and bounds;
- DXF: units, polyline/vertex counts, and bounds;
- SVG: view box and path structure;
- JSON: units and curve/point/marker counts.

Measurements appear in the command result. Project generators additionally get
a stable `<generator>.measurements.json` beside their artifacts.

## Analytic References

Every generator declares `volume_analytic` or `area_analytic` independently of
its kernel. Exact 3D kernel/reference comparisons use 1e-6 relative tolerance.
Tessellated, faceted, 2D approximated, or explicitly approximate references use
1% unless a generator contract tightens it. STEP re-import agrees with the
native kernel measurement to 1e-6. Meshes must be watertight when they represent
a closed 3D solid.

`cadctx verify <generator>` applies the relevant checks by kind and declared
formats. A failed required check is an error. An unavailable optional external
tool produces `degraded` only when every available check passes.

## JSON Coordinate Payload

The optional JSON artifact contains generator-owned coordinates and annotations,
not viewer-derived geometry. Coordinates use millimetres on the same datum as
SVG, DXF, and any associated 3D sections. Measurements remain separate from
geometry payloads.
