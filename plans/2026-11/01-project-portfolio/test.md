# Verification

Native Windows verification, 2026-11-01/02:

- `uv run --extra default pytest -o addopts= -q`: 112 passed, 2 skipped in 9.85 s.
  Skips: optional OpenSCAD and unavailable Windows symlink creation.
- `uv run --extra default ruff check .`: all checks passed.
- `corepack pnpm check`: 27 files, zero errors/warnings/hints.
- `corepack pnpm test`: 11 passed, including explicit allowlist and confinement.
  Node symlink test branch reports Windows EPERM; lexical confinement tested.
- `corepack pnpm build`: pass; existing large 3D viewer bundle warning.
- Chrome at `/project`: live GLB views, SVGs/images and sandboxed historical HTML
  render. Fixed initial viewport height and Windows subprocess encoding issues.
- Actual CAD comparison overlay rendered; it exposes a missing lower smile in
  the external model. This is a model parity failure, not a portfolio delivery pass.
- Final Python regression covers coordinate-independent mesh bounds at origin
  and large positive/negative translations. Exact STEP tolerances unchanged.

Operational logs: `.cache/reports/portfolio-final-pytest.out`,
`portfolio-final-ruff.out`, `bear-web.out`, `web.log`.

Model migration remains incomplete: front STEP check fails; both historical
volume checks fail. Draft status is visible and elephant migration remains deferred.

After restarting cadcon web on 2026-11-02, HTTP checks passed for 20 declared
page/assets/models, including legacy download links. Undeclared parameters and
Python-source requests returned 404. Evidence: `.cache/reports/portfolio-http.json`.
Fresh browser capture was unavailable because the browser access host was offline;
the earlier Chrome visual inspection remains the visual evidence.
