# Exchange Formats

Backends share behavior through files, never through each other's object
models. This specification defines what each backend must emit and what those
files mean.

## Conventions

- **Units are millimetres** in every format. DXF declares `$INSUNITS = 4`;
  STEP, STL, GLB, SVG and the coordinate payload carry millimetre values.
- **Coordinate frames**: 3D parts are built Z-up, 2D parts Y-up in the XY
  plane. The origin is the part's **declared datum** — the point its parameters
  are defined against — and a generator states that datum in its parameter
  model. For a plate or a bracket the datum is the minimum corner; for an
  airfoil it is the leading edge of the camber line with the chord line on
  y = 0, and the outline may reach marginally beyond it. Inventing a different
  origin per format is forbidden: every format of one generator carries the
  same datum.
- **Formats are the contract boundary.** A backend joins the repository by
  honoring the formats below; it never has to match another backend's API,
  and no code outside a backend module interprets that backend's native
  objects.

## Required Outputs Per Path

| Path | Required | Also emitted |
| --- | --- | --- |
| 2D generator | SVG **and** DXF | JSON coordinate payload |
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

## The JSON Coordinate Payload

SVG and DXF are drawings; the `json` format is the same geometry as **data**,
for a consumer that must draw its own axes, overlays and annotations rather
than display a finished picture. A generator that has curves worth plotting
publishes one; the exporter writes it verbatim and interprets nothing.

```jsonc
{ "kind": "profile", "units": "mm", "chord": 120.0,
  "bounds": [minx, miny, maxx, maxy],
  "curves":  [{ "id": "outline", "role": "surface", "closed": true, "points": [[x, y], …] }],
  "markers": [{ "id": "max_thickness", "label": "…", "segment": [[x, y], [x, y]] }] }
```

- Coordinates are millimetres on the generator's datum, identical to the ones
  the SVG, DXF and any 3D section wires are built from — one computation, many
  formats. A consumer that redraws these points is reading the generator.
- The payload carries geometry and annotation only. Measurements belong in the
  result file's `metrics`, never here, and geometry never travels as a metric.

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
- SVG files: structural check (view box present, expected path count);
- JSON payloads: re-read, curve, point and marker counts and declared units
  measured.

Measurements land in the command's result file under `measurements`.

## Cross-Backend Agreement

Backends that build the same reference part must agree. Each generator declares
an analytic volume (or area) computed from its parameters alone; that analytic
value is the reference, not another backend's output.

- Generators that build the same part on different backends declare a shared
  **family**. Only one family is compared at a time: an analytic reference
  belongs to a part, not to the repository, so comparing across families would
  be meaningless.
- Kernel volumes agree with the analytic value to within 1e-6 relative.
- Tessellated and faceted volumes agree with it to within **1%**.
- Where a closed form is exact only over part of the parameter space, the
  generator says so and the comparison quotes the parameters it ran at. Outside
  that range the backends must still agree **with each other** — losing
  exactness must never quietly become losing agreement.
- `cadctx compare --family <name>` measures this across every installed backend
  of that family and fails the tolerance check loudly rather than averaging
  disagreement away.
