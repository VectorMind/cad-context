# Exchange Formats

Backends share behavior through files, never through each other's object
models. This specification defines what each backend must emit and what those
files mean.

## Conventions

- **Units are millimetres** in every format. DXF declares `$INSUNITS = 4`;
  STEP, STL, GLB and SVG carry millimetre values.
- **Coordinate frames**: 3D parts are built Z-up in their own frame with the
  part's minimum corner at the origin. 2D parts are built Y-up in the XY plane
  with the outline's minimum corner at the origin.
- **Formats are the contract boundary.** A backend joins the repository by
  honoring the formats below; it never has to match another backend's API,
  and no code outside a backend module interprets that backend's native
  objects.

## Required Outputs Per Path

| Path | Required | Also emitted |
| --- | --- | --- |
| 2D generator | SVG **and** DXF | — |
| 3D B-rep backend (OCCT: CadQuery, build123d) | STL **and** GLB | STEP |
| 3D CSG backend (OpenSCAD) | OpenSCAD source (`.scad`) | STL and GLB when the binary is resolvable |

- **GLB is the web-app bridge.** Every 3D path ends in GLB so a viewer renders
  any backend's output without knowing which kernel produced it. GLB is derived
  from the path's STL through the mesh layer.
- **STEP is emitted wherever the kernel supports it**, as the lossless
  interchange format for external CAD tools.
- A backend whose external prerequisite is missing **degrades, never fails**:
  it emits what it can (for OpenSCAD, the `.scad` source), records the skipped
  formats with a reason in its result file, and reports `degraded` status.

## Tessellation

Mesh exports from a B-rep kernel use a linear tolerance of 0.01 mm and an
angular tolerance of 0.1 rad. Faceted CSG primitives use a facet count high
enough that faceting error stays an order of magnitude below the agreement
tolerance below.

## Proof Of An Export

An export counts as delivered only when it is measured, never when it merely
exists. Every written artifact is loaded back and checked:

- mesh files (STL, GLB): volume, surface area, watertightness, bounding box,
  vertex and face counts;
- STEP files: re-imported through a kernel, volume and bounding box measured;
- DXF files: re-read, polyline and vertex counts and bounds measured, units
  confirmed;
- SVG files: structural check (view box present, expected path count).

Measurements land in the command's result file under `measurements`.

## Cross-Backend Agreement

Backends that build the same reference part must agree. Each generator declares
an analytic volume (or area) computed from its parameters alone; that analytic
value is the reference, not another backend's output.

- Kernel volumes agree with the analytic value to within 1e-6 relative.
- Tessellated and faceted volumes agree with it to within **1%**.
- `cadctx compare` measures this across every installed 3D backend and fails
  the tolerance check loudly rather than averaging disagreement away.
