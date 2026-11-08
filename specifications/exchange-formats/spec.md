# Exchange Formats And Verification

## Boundary

Shared behavior crosses backend boundaries only through files. No module outside
a generator or exporter interprets a backend-native object. Units are
millimetres; 3D is Z-up; 2D is Y-up on the generator's declared datum.

SVG maps CAD Y-up coordinates into its downward display axis so positive Y
appears above the datum. Its view box encloses the transformed geometry with
the usual margin. DXF and JSON retain the original CAD coordinates.

| Generator path | Required outputs | Additional output |
| --- | --- | --- |
| 2D Shapely | SVG and DXF | JSON coordinate payload when useful |
| 3D build123d B-rep | STL and GLB | STEP, opt-in single-piece 3MF |
| Optional OpenSCAD project | SCAD source | STL and GLB when its binary resolves |

GLB is derived from STL through trimesh. STEP is the lossless B-rep interchange
format. A missing external OpenSCAD binary degrades to SCAD-only output and
records every skipped format; it does not crash generation.

For explicitly coloured native build123d assemblies, the exporter tessellates
leaf parts separately, preserving their global assembly locations and assigning
named opaque matte PBR materials. Native palette colours are interpreted as
sRGB and converted to linear glTF base-colour factors. Uncoloured shapes retain
the existing single-mesh STL bridge. Colour is presentation data and never
implies filament/material settings in print packages. The viewer preserves
authored GLB materials and uses its default lit surface only when no materials
were authored; missing normals and wireframe must not erase colours.

## Tessellation

build123d meshes use 0.01 mm linear and 0.1 rad angular tolerance. OpenSCAD
project generators choose enough facets to remain inside the 1% mesh agreement
budget.

## Round-Trip Measurements

Every generated format is re-read when measurement is enabled:

- STL/GLB: volume, area, watertightness, bounds, vertices, and faces;
- STEP: build123d re-import, volume, area, and bounds;
- 3MF: independent ZIP/XML resource/build/unit inspection and trimesh topology,
  signed volume, bounds, vertices and faces after applying the build transform;
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

`cadcon verify <generator>` applies the relevant checks by kind and declared
formats. A failed required check is an error. An unavailable optional external
tool produces `degraded` only when every available check passes.

## JSON Coordinate Payload

The optional JSON artifact contains generator-owned coordinates and annotations,
not viewer-derived geometry. Coordinates use millimetres on the same datum as
SVG, DXF, and any associated 3D sections. Measurements remain separate from
geometry payloads.

## Single-Piece 3MF

Build123d Mesher/lib3mf writes directly from one native solid with explicit
millimetre units and the shared tessellation tolerances. A fresh Mesher is used
per artifact. Exactly one mesh and one direct printable build item are required;
valid unused component resources produced by Mesher are permitted. Multiple
solids fail; physical pieces use separate generators. No slicer profile or
new backend is introduced. See `specifications/3mf-export/spec.md`.

Independent package and topology validation happens before atomic replacement,
even when optional measurement reporting is disabled. Invalid geometry raises
an error and preserves the previous artifact. Missing runtime support is an
explicit generation skip; missing requested/declared B-rep artifacts make
verification fail. Only OpenSCAD STL/GLB rendering is an optional external skip.
`verify -f 3mf` selects 3MF explicitly, while project declarations include it in
default verification. Its volume must match native and analytic values within
1%; bounds must match native values at 1% relative or 1e-6 mm absolute near zero.
Accompanying STL measurements never substitute for 3MF measurements.
# Generator export quality

A generator may return `BuildResult(..., tessellation=Tessellation(...))` using
`cad_context.types.Tessellation`. Both deflections must be finite and positive.
STL, GLB (through STL), and build123d Mesher 3MF receive the supplied linear and
angular deflections. The default remains 0.01 / 0.1 when no profile is supplied.
These values are passed to the maintained kernel/exporter APIs; they do not
change native B-rep geometry or verification tolerances. Project measurement
sidecars and API summaries record the profile. Models may use separate preview
and print generators when fine sampling creates large artifacts. A profile is
not a print/material setting and never authorizes mesh repair.

`Tessellation(stl_writer="mesher")` explicitly selects build123d's native
Mesher/lib3mf STL writer instead of the default OCCT STL writer. Both receive
the same deflections. Use this when measured fine features require the native
Mesher path; it does not authorize post-export triangle cleanup. GLB continues
to derive from that STL. The selected writer is recorded in non-default quality
profiles; omitted selection preserves the existing default behavior and payload.
