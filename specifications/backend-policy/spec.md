# Backend Policy

## Maintained Geometry Paths

`cad-context` keeps one efficient default construction path per ordinary model.
The maintained B-rep backend is **build123d**. It provides exact OCCT solids,
STEP export, Python-native composition, and direct integration with the shared
parameter and analytic-reference contracts.

Shapely remains the maintained 2D geometry path. Trimesh remains the mesh
inspection and GLB bridge. OpenSCAD/SolidPython2 remains an optional project
authoring toolchain when `.scad`, Customizer delivery, or a genuinely different
CSG/mesh path is a requirement.

External projects are repository-independent when they use this supported
toolchain. Arbitrary project-specific Python dependencies and isolated project
environments are outside the workbench contract.

## Debt And Validation Policy

Ordinary models are not multiplied across wrappers merely to demonstrate
equivalence. CadQuery and build123d share OCCT, so maintaining both continuously
does not supply an independent geometric engine. The independent evidence for
every model is instead:

- kernel-independent parameter and derived-geometry calculations;
- an analytic volume or area where one is meaningful;
- exact kernel measurements where available;
- re-imported exchange files and measured meshes.

An additional backend is justified only by a concrete deliverable or risk: a
backend-specific customer format, a failure-prone operation, an unavailable
analytic reference, a dependency/kernel upgrade checkpoint, or manufacturing
risk that warrants independent reconstruction. Such a check belongs in the
model project and does not become permanent core maintenance by default.

## Alternative Reconstruction Contract

An alternative implementation can be reconstructed without changing the shape
contract:

1. Reuse or translate the project's kernel-independent parameter model,
   derived profiles/sections, analytic reference, datum, and bounds.
2. Add a project generator whose module exports `build(params) -> BuildResult`.
   Import its kernel inside `build`; the builder writes no files.
3. Declare its id, backend, formats, parameter-model class, defaults, and web
   exposure in `project.yaml`.
4. Keep native-object interpretation inside that backend module. Cross the
   workbench boundary only through STEP, STL, GLB, SVG, DXF, JSON, or SCAD.
5. Run the same format-aware verification: exact kernel/reference agreement
   where the reference is exact, STEP re-import, and mesh/DXF/SVG/JSON proof.

CadQuery reconstruction requires an isolated compatible environment because
its OCP package conflicts with build123d's OCP distribution. It is not a
supported dependency of the core workbench. The original backend evaluation
and measured reference results are recorded in the dated packets under
`plans/2026-08/11-cad-generators-bringup/` and
`plans/2026-08/11-airfoil-parametric-visualizer/`.

