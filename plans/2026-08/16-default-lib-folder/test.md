# Test Proof: Default Library And Project Folder Workflow

This packet contains the original planning-review record followed by final
runtime proof for the completed implementation, per `WORKFLOW.md` § Test Proof.

## Decision Pass Applied (2026-08-16, later same day)

The maintainer answered all thirteen OPs as free-text bullets. Consistency
checks on the finalized plan:

| Check | Expected | Actual |
| --- | --- | --- |
| Resolutions recorded | OP-501…OP-513 carry the maintainer's resolution verbatim in intent, marked `accepted` (OP-502/511 as modified, OP-504 as mechanism-dropped) | as expected |
| Summary table sync | Resolution summary table matches every detailed OP section's status and resolution | as expected |
| Strengthened cleanup captured | Variant code is dropped (not frozen); spec keeps rationale + regeneration recipe; previous plans remain the historical record | as expected |
| Multitudes rule supersession | Explicitly stated in a dedicated section; docs-sweep risk listed; narrowed durable form (exchange-format contracts stay) preserved | as expected |
| Residual OPs | Three new points (OP-514 exposure, OP-515 removal scope, OP-516 compare fate) tabled with candidates, proposal, confidence, status | as expected |
| Phase gating | Phases reordered so specs capture recipes before any deletion; phases 1–2 gated on OP-515/516, phase 5 on OP-514 | as expected |
| No premature edits | No source, dependency, or spec files changed; planning documents only | as expected |

## Second Decision Pass Applied (2026-08-16)

The maintainer answered the three residual points. Consistency checks:

| Check | Expected | Actual |
| --- | --- | --- |
| OP-514 | `project.yaml` exposure block accepted; recorded with unchanged validation rules (names only) | as expected |
| OP-515 | Recorded as modified: OpenSCAD live behind its flag as optional export; CadQuery removed entirely (code, extra, pins, override hack, probe); recovery info in README and/or spec; `.scad`-authorship nuance stated (not derivable from OCCT solids) | as expected |
| OP-516 | Repurpose accepted with rename; proposed name `cadctx verify`, flagged as a review-time naming detail, not a blocking OP | as expected |
| Ledger closed | Resolution summary shows all 16 OPs accepted; no gating text remains in phases, non-goals, risks, or exit criteria | as expected |
| No premature edits | Planning documents only; no source or dependency files changed | as expected |

## Initial Planning Checks (2026-08-16)

| Check | Expected | Actual |
| --- | --- | --- |
| Packet shape | `plan.md` + `test.md` present; no `implementation.md` before implementation | as expected |
| Plan shape | Problem summary → resolution summary table → goal/objectives → scope/non-goals → open points → phases → dependencies/risks → exit criteria | as expected |
| Resolution summary table | One row per OP with topic, proposal, confidence, status; matches the detailed Open Points section (13 OPs, OP-501…OP-513) | as expected |
| OP numbering | Continues after the external cache-barriere packet's OP-4xx range (handoff cites OP-408); no collision with OP-1xx/2xx/3xx from the three bringup packets | as expected |
| OP format | Every OP lists candidates with a short argument each, names a proposal, carries confidence (high/medium/low) and status | as expected |
| Handoff traceability | OP-501 adopts handoff OP-408; OP-504/505/510 cover the handoff's follow-up items (preferred implementation, validation level, stale memoization); the lean SDD workflow is carried by OP-513 | as expected |
| Grounding against code | Claims checked against current sources: OCP conflict workaround in `pyproject.toml` (`override-dependencies`), fixed geometry paths in `src/cad_context/workspace.py`, single-root artifact serving and lifetime memoization in `webapp/src/server/cadctx.ts` and `webapp/src/pages/api/artifact/[...file].ts`, no cache-barriere trace anywhere in `src/` (grep) | as expected |
| Repo rules respected | No dependency file edited (OPs not yet accepted); no git commands run; no generated files outside `plans/` | as expected |
| Index update | `plans/open.md` lists this packet as open | as expected |

## Planning Fixtures Referenced

- `C:\Users\wassi\OneDrive\Partage Wassim Mezri\15-cache-barriere\handoff.md`
  — basis document (read only).
- `C:\Users\wassi\OneDrive\Partage Wassim Mezri\cache-barriere` — phase-6
  dry-validation target; no generation was performed there.

## Known Gaps

- Real OneDrive generation and sync-lock behavior remain unmeasured because
  the authorized acceptance check was deliberately non-writing. Copied-project
  generation and live serving cover the application path without altering the
  user's evidence folder.

## Implementation Proof (2026-08-16)

### Dependency surface

| Command | Expected | Actual |
| --- | --- | --- |
| `uv lock` | lock resolves without the CadQuery project or override | 72 packages resolved; no `cadquery`, numba, or `override-dependencies`; build123d's required `cadquery-ocp-novtk` remains |
| `uv sync --extra default` | lean documented install | success; removed CadQuery, numba, VTK/trame stack, SolidPython2, and the former VTK OCP wheel; installed build123d's novtk OCP wheel |
| `uv sync --extra all` | optional OpenSCAD authoring layer remains installable | success; added only `solidpython2`, `ply`, and `setuptools` |

### Static and automated checks

| Command | Actual |
| --- | --- |
| `uv run ruff check .` | all checks passed |
| `uv run pytest` | **75 passed** in 6.89 s |
| `corepack pnpm check` | 23 files; 0 errors, warnings, or hints |
| `corepack pnpm test` | **10 passed** |
| `corepack pnpm build` | production server/client build completed; existing non-blocking >500 kB ModelView chunk warning remains |

### Built-in discovery and format-aware verification

`cadctx --no-project info`, `generators`, and `paths` reported repository mode,
four supported backends (`shapely`, `build123d`, `openscad`, `trimesh`), and four
built-in generators.

| Generator | Result | Reference | Native | Checks |
| --- | --- | ---: | ---: | --- |
| `plate2d` | ok | 8,296.345145 mm² | 8,296.404436 mm² | 5/5: analytic, native tolerance, DXF units/geometry, SVG |
| `airfoil` | ok | 1,177.349093 mm² | 1,177.349093 mm² | 6/6: analytic, native, DXF, SVG, JSON |
| `bracket-build123d` | ok | 48,713.628421 mm³ | 48,713.628421 mm³ | 5/5: exact native, watertight mesh, mesh tolerance, STEP re-import |
| `wing-build123d` | ok | 230,760.422171 mm³ | 230,663.611210 mm³ | 5/5: declared approximate reference within 1%, watertight mesh, STEP re-import |

### External project fixture

A fresh copy of `tests/fixtures/sample_project` under `.cache/scratch/` proved:

- merged discovery: four built-ins plus `project-plate` and
  `project-openscad-box`;
- project manifest defaults (`width=75`) reflected in the schema;
- generation and verification wrote stable SVG, DXF, and
  `project-plate.measurements.json` under the copied project's `cad/`;
- `project-plate` passed 5/5 checks at exactly 2,250 mm²;
- unit tests proved collision hard-stop, no-clobber/dry-run init, pointer
  precedence and bypass, no project `__pycache__`, and OpenSCAD source-only
  degradation when its binary is unavailable.

### Live web acceptance

`cadctx --project <copied-fixture> web --no-install --port 4399` started through
the documented surface. Because 4399 was already occupied, Astro selected 4400
and `cadctx` detected that actual URL. Over HTTP:

- `/api/generators.json` listed `project-plate` under `sample-project` with
  editable `width`;
- `POST /api/generate` returned `ok` for `width=82`;
- the returned project SVG route responded **200**, `image/svg+xml`, 404 bytes;
- the temporary server was stopped and port 4400 no longer answered.

### Real evidence-folder dry validation

`cadctx project init "C:\Users\wassi\OneDrive\Partage Wassim
Mezri\cache-barriere" --dry-run` returned `ok project-init — project scaffold
preview`. A subsequent read confirmed `project.yaml` was not created and the
folder still contained only the original `dimensions.md` and image evidence.
