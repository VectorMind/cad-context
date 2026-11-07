# Validation

Scratch exact same rounded head: 0.0001 linear / 0.02 angular deflection passes
independent actual 3MF checks. Default 0.01 / 0.1 fails; intermediate profiles
tested also failed. No triangle removal, winding repair or curve change.

Final native Windows results:

- `uv run --extra default pytest -o addopts= -q`: 118 passed, 2 skipped in 11.67 s.
  Skips: optional OpenSCAD and Windows symlink privilege unavailable.
- Ruff and `git diff --check`: pass.
- Web check: 27 files, zero diagnostics; 11 tests passed; build passed with
  existing large viewer chunk warning.
- Actual external head print `cadcon verify`: 18/18, STEP and 3MF. Native
  21115.1421576 mm3, approximate independent reference 21115.1373452 mm3,
  mesh 21114.6610919 mm3; all units/references/transforms/topology/bounds checks pass.
- Profile metadata in project sidecar: linear_deflection 0.0001,
  angular_deflection 0.02. Actual mesh: 1,571,222 vertices / 3,142,440 faces.
- Regression proves default and explicit quality reach STL and actual Mesher
  exports, native geometry remains unchanged, and invalid profiles fail.

Logs: `.cache/reports/tessellation-pytest.out`; CLI result
`.cache/results/verify-animal-puzzle-bear-rounded-front-print.json`.
Visual browser interaction unavailable; actual CAD SVG rendered and inspected.
No remaining generic implementation gaps. Large output/validation costs are explicit.

Final restarted preview: 39 declared pages, evidence files and artifact downloads
returned HTTP 200; two undeclared source paths returned 404. Schema endpoint
publishes the 1.5 / 0.5 mm radius defaults. Download-only head print entry is listed
with STEP/3MF and no model-view link. Evidence: `.cache/reports/portfolio-http.json`.
