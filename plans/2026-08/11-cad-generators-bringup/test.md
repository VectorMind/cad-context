# Test Proof — CAD Generators Python Environment Bringup

Status: implemented and proven 2026-08-11. Planning-stage checks are kept below
for the record; runtime proof follows.

## Environment

- Windows 11, PowerShell; uv 0.11.19; Python 3.12.13 (pinned by
  `.python-version`).
- `uv sync --extra all` → 106 packages. Key versions: cadquery 2.8.0,
  build123d 0.11.1, cadquery-ocp 7.9.3.1.1, trimesh 5.0.0, manifold3d 3.5.2,
  ezdxf 1.4.4, shapely 2.1.2, numba 0.66.0, numpy 2.4.6.
- Reproducibility note: a bare resolve fails twice over — see the dependency
  conflicts in `implementation.md`. Both fixes are in `pyproject.toml`, so a
  clean `uv sync --extra all` succeeds from the committed files alone.
- OpenSCAD 2021.01 provisioned by `cadctx fetch openscad` to
  `.tools/openscad/openscad-2021.01/openscad.exe`.

## Fixtures

No checked-in geometry fixtures. Every check regenerates its geometry and
compares against a closed-form value computed from the parameters
(`generators/models.py`: `bracket_volume`, `plate_area`). Tests redirect the
workspace cache into `tmp_path` via `CAD_CONTEXT_CACHE`.

## Commands Run

```bash
uv sync --extra all
uv run cadctx fetch openscad
uv run cadctx info
uv run cadctx demo
uv run cadctx compare
uv run cadctx generate plate2d -p width=160 -p slot_count=5
uv run cadctx generate bracket-cadquery -p width=120 -p hole_diameter=10 -f glb
uv run pytest
uv run ruff check .
```

## Exit Criterion 1 — `uv sync --extra all` on Windows

Expected: clean install of all extras. Actual: succeeded (106 packages) after
the two dependency pins recorded in `pyproject.toml`; both kernels import in
the same interpreter (`cq 2.8.0 b3d 0.11.1`).

## Exit Criterion 2 — `cadctx fetch openscad`

Expected: download, unpack and resolve an executable into `.tools/` from
`config/artifacts.yaml` alone.

Actual:

```text
ok fetch — openscad: installed
  openscad: .tools/openscad/openscad-2021.01/openscad.exe
  result: .cache/results/fetch.json
  report: .cache/reports/fetch.log
```

The asset (`OpenSCAD-2021.01-x86-64.zip`) was matched by pattern from release
tag `openscad-2021.01`; the transcript went to the report file, not the
console. A first attempt with tag `2021.01` failed as designed — one line,
`error fetch — ArtifactError: GitHub API 404`, exit code 1, full traceback in
`.cache/reports/fetch.log`.

## Exit Criterion 3 — Artifacts at fixed `.cache/cad/` paths

`cadctx demo` → `ok demo — 4/4 generators clean, 11 artifacts`. Files written
(sizes from a clean run):

| Path | Bytes |
| --- | --- |
| `.cache/cad/plate2d/plate2d.svg` | 29 257 |
| `.cache/cad/plate2d/plate2d.dxf` | 81 742 |
| `.cache/cad/bracket-cadquery/bracket-cadquery.step` | 36 670 |
| `.cache/cad/bracket-cadquery/bracket-cadquery.stl` | 102 684 |
| `.cache/cad/bracket-cadquery/bracket-cadquery.glb` | 37 812 |
| `.cache/cad/bracket-build123d/bracket-build123d.step` | 36 608 |
| `.cache/cad/bracket-build123d/bracket-build123d.stl` | 102 684 |
| `.cache/cad/bracket-build123d/bracket-build123d.glb` | 37 816 |
| `.cache/cad/bracket-openscad/bracket-openscad.scad` | 511 |
| `.cache/cad/bracket-openscad/bracket-openscad.stl` | 252 299 |
| `.cache/cad/bracket-openscad/bracket-openscad.glb` | 28 960 |

SVG, DXF, STEP, STL and GLB are all present. Paths are stable across runs:
`test_regenerating_reuses_the_same_paths` regenerates with different parameters
and asserts the returned file map is identical.

Result summaries were written for every command
(`.cache/results/<command>.json` + `.md`, plus `last.*`); console output for
the whole sequence above was 5 lines or fewer per command.

## Exit Criterion 4 — Measured properties, not "looks right"

Every artifact is loaded back and measured. Bracket at default parameters
(80×60×50, t=6, ⌀8); analytic volume **48 713.6284 mm³**:

| Backend | Kernel volume | Mesh volume (STL) | Watertight | Mesh bounds max | Faces |
| --- | --- | --- | --- | --- | --- |
| CadQuery | 48 713.62842 | 48 714.128 | yes | (80, 60, 50) | 2 052 |
| build123d | 48 713.62842 | 48 714.128 | yes | (80, 60, 50) | 2 052 |
| OpenSCAD | — (no in-process kernel) | 48 714.492 | yes | (80, 60, 50) | 1 572 |

STEP round-trip (re-imported through OCCT): both B-rep backends re-measure at
48 713.6284 mm³ with bounds max (80, 60, 50) — lossless.

GLB round-trip: `test_3d_exports_round_trip_and_measure` re-loads each GLB and
requires its volume to match the STL's to 1e-6 relative.

2D plate at `width=160, slot_count=5`:

- shapely area 10 739.3879 mm² vs analytic 10 739.2655 mm² → 1.1e-5 relative
  (arc faceting in the polygon approximation).
- DXF re-read: 10 polylines (1 outline + 5 slots + 4 holes), 1 294 vertices,
  bounds (0, 0, 160, 80), `$INSUNITS` = 4 (mm).
- SVG: 29 251 bytes, 1 path, view box present.

## Exit Criterion 5 — Cross-backend agreement within 1%

```text
ok compare — 3 backends, max deviation 0.0018% vs analytic (tolerance 1.0%)
```

Max deviation **1.77e-5** (0.0018%), from mesh tessellation and OpenSCAD's
96-facet cylinders — three orders of magnitude inside the 1% budget. Kernel
volumes agree with the analytic value to 1e-13 relative.

## Exit Criterion 6 — `pytest` and `ruff` clean

```text
50 passed in 6.41s
All checks passed!
```

Coverage by file: parameter-schema contract and validation (`test_params.py`);
API purity, analytic agreement and error handling (`test_api.py`); export
round-trips, fixed paths, STEP/DXF/SVG/GLB measurement and OpenSCAD graceful
degradation (`test_exchange.py`); CLI result files, quiet-console budget,
JSON/quiet modes, fixed-path regeneration, failure exit codes (`test_cli.py`);
workspace layout, result/report writing and artifact declarations
(`test_workspace.py`). The three bracket tests are parametrised over whichever
3D backends are installed, so a partial install still proves what it has.

## Exit Criterion 7 — Every command documented

`README.md` documents all nine commands (`info`, `generators`, `schema`,
`generate`, `demo`, `compare`, `fetch`, `paths`, `clean`) with a usage line and
a runnable example, plus the global `--json` / `--quiet` options — verified by
reading the CLI's command list against the README section headings.

## Behavior Checks Beyond The Exit Criteria

- **Graceful degradation**: with the OpenSCAD resolver monkeypatched to `None`,
  `bracket-openscad` still writes `.scad`, reports STL and GLB as skipped with
  the reason "OpenSCAD binary not found", and does not raise
  (`test_openscad_degrades_to_source_when_the_binary_is_absent`).
- **Failures produce results**: `cadctx generate plate2d -p width=-5` exits 1,
  prints 3 lines, and leaves a `status: error` result file plus a traceback
  report (`test_bad_parameter_fails_with_a_result_file_and_exit_code`).
- **The Python API writes nothing**: `test_api_build_writes_nothing` snapshots
  the cache tree before and after `api.build(...)` for every 3D backend and
  requires it to be unchanged.
- **GLB alone**: requesting only `-f glb` tessellates through a temporary file
  and leaves exactly one artifact in the output directory.

## Known Gaps

- No visual verification of the SVG or the 3D renders; proof is structural and
  metric only. The Plan 2 web app is the intended visual surface.
- `.tools/` provisioning is exercised on Windows only; the Linux AppImage and
  macOS DMG entries in `config/artifacts.yaml` are declared but untested, and
  the DMG entry in particular is a declaration, not a working mount+extract
  path.
- No performance measurements (generation latency feeds Plan 2's OP-204
  go/no-go and is not measured here).
- Mesh measurement relies on trimesh alone; no independent validator
  cross-checks watertightness or volume.
- STEP round-trip uses CadQuery's importer for both B-rep backends; build123d's
  own importer is not exercised.

## Planning-Stage Checks (2026-08-11)

- `plan.md` follows the WORKFLOW.md plan shape (problem, goal, scope, open
  points, phases, dependencies, exit criteria): yes.
- Every dependency-selecting open point (OP-101…OP-107) lists candidate
  options, a proposal, a confidence level, and a status: yes.
- No `implementation.md` created (no implementation yet): correct at the time;
  created once Phase 1 work landed.
- Proposed `pyproject.toml` sketch is consistent with the open points and
  with the evidence-engine conventions (uv, optional-dependency groups,
  dev group): checked by review.

## Acceptance Review (2026-08-11)

- Maintainer accepted OP-101…OP-107; OP-103 amended (config-driven GitHub
  releases fetch script for external binaries) and OP-106 amended (CLI as
  the single documented human/agent interface, no skills). Plan updated:
  status header, Resolution Summary table, per-OP statuses, amendments,
  phases, risks, and exit criteria all reflect the accepted state
  consistently — checked by re-read.
- OP-103 feasibility verified at planning level: official OpenSCAD releases
  on `github.com/openscad/openscad` carry Windows x86-64 assets reachable
  via the GitHub releases API; nightly builds are on openscad.org, covered
  by the direct-URL fallback in the config schema.
- OP-108 raised and accepted at the start of implementation (execution output
  under `.cache/`, quiet console, fixed geometry paths, side-effect-free Python
  API). Plan table, OP section and exit criteria updated; rules folded into
  `specifications/workspace-layout/spec.md` and
  `specifications/agent-interface/spec.md`.
