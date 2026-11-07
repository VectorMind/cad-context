# Native 3MF export

Status: implemented, 2026-11-01; acceptance evidence is recorded in
plans/2026-11/01-native-3mf-export/test.md.
This extends specifications/exchange-formats/spec.md.

## Selected design

Support generic 3MF for build123d generators through the existing cadcon generate and verify commands and cad_context.exchange.export boundary. Use build123d.Mesher backed by lib3mf. This is not a new CAD backend, an external converter service, or a slicer integration. Start with the existing lock (build123d 0.11.1, lib3mf 2.5.0); verify the installed API on Windows before changing dependencies.

Default units are explicitly millimetres, Z-up, with 0.01 mm linear and 0.1 rad angular tessellation tolerances. Export directly from the native shape; do not round-trip through STL. Instantiate a fresh Mesher for each artifact to avoid accumulated objects. Stable paths and atomic writes follow the existing exchange contract.

The initial 3MF delivery contract accepts a single solid per generator and produces exactly one printable mesh object and one build item. Reject multi-solid print requests explicitly; assembled previews use existing STEP/GLB formats. Separate physical pieces are separate generators sharing construction helpers. Do not silently select the first solid or merge disconnected pieces into one object.

Include 3mf in applicable format validation, exporter dispatch, measurement and verification, capability reporting and README documentation. Use the existing format selection interface; no new top-level conversion command is required. Do not add 3mf to built-in generators automatically.

## Measurements and failure behavior

Read the actual 3MF archive and mesh back. Verify explicit mm units; object/build counts; valid resource references; transforms; finite coordinates and valid indices; connectedness; edge manifoldness; watertightness; outward consistent winding and positive signed volume; duplicate/degenerate triangles; vertex/face counts; bounds and volume against native/reference values. Use independent ZIP/XML inspection and trimesh-based geometric measurement in addition to the native lib3mf round-trip acceptance test. Valid unused
component resources emitted by Mesher are permitted; the build item must
reference the sole printable mesh directly. A scene loader must apply instance transforms exactly once.

Use 1% maximum agreement for mesh/reference quantities; preserve the existing 1e-6 exact native/STEP checks. For near-zero quantities use justified absolute tolerances. Do not repair arbitrary topology automatically. Keep measurement results in normal CLI JSON and project measurements files.

Mesh bounds compare absolute coordinate errors against a translation-invariant
per-axis budget: max(1e-6 mm, min(linear tessellation deflection, 1% of native
axis extent)). Coordinate-relative tolerances are unsuitable at the origin and
would allow excessive errors for far-translated models. Export and verify use
the same budget; this does not change exact STEP or historical parity tolerances.

Missing optional runtime support must be reported explicitly through existing unavailable/skipped conventions. A required 3MF missing or failing verification cannot yield an all-passed delivery claim. Malformed geometry is a failed check, not an optional dependency skip. Surface this distinction in tests and docs.

## Integration boundaries

No model-specific paths, data, identifiers or construction logic belong in this workbench feature. Keep API builds free of file writes. Verify confinement and atomic replacement in external projects, and preserve existing exporters. No new web geometry logic: include 3MF download handling only if current generic artifact handling requires a change.

Native Windows is the required acceptance platform for this handoff. Use Windows uv/Python only against the Windows .venv. The portable implementation may continue supporting other platforms, but Linux results do not substitute for Windows acceptance.

## Sources checked 2026-11-01

- https://build123d.readthedocs.io/en/v0.11.0/import_export.html
- https://build123d.readthedocs.io/en/stable/import_export.html
- https://build123d.readthedocs.io/en/latest/_modules/mesher.html
- https://github.com/3MFConsortium/lib3mf
- Local uv.lock and src/cad_context/exchange/.

Online current documentation is supporting evidence. Confirm signatures against locked installed 0.11.1 rather than adopting development APIs blindly.
