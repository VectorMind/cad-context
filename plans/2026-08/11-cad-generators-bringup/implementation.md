# Implementation Log — CAD Generators Python Environment Bringup

## Progress

`▰▰▰▰▰▰ Done`
Phases 1–5 landed: environment, 2D smoke, 3D smoke on three backends, measured
proof, and the spec fold. Follow-ups are non-blocking and listed at the end.

## Files Added

Package (`src/cad_context/`):

| File | Role |
| --- | --- |
| `workspace.py` | `.cache/` layout resolution (`results`, `reports`, `cad`, `scratch`), root/cache env overrides, display paths |
| `results.py` | `Result` dataclass, `<command>.json` + `.md` writers, `last.*` pointers, the minimal console rendering |
| `params.py` | parameter-schema contract: `number/integer/choice` fields, `describe()` flattening, `key=value` override parsing |
| `types.py` | `BuildResult` (native object + metrics, never a file), `BackendUnavailable` |
| `backends.py` | availability probing via `find_spec` (never imports a kernel to answer), version and binary status |
| `artifacts.py` | `config/artifacts.yaml` loader, GitHub-release/direct-URL fetch, unpack, `.tools/`-then-`PATH` resolution |
| `api.py` | side-effect-free Python surface for agents/scripts |
| `cli.py` | `cadctx`: `info`, `generators`, `schema`, `generate`, `demo`, `compare`, `fetch`, `paths`, `clean` |
| `generators/models.py` | `BracketParams`, `PlateParams`, and the analytic volume/area formulas used as the cross-backend reference |
| `generators/plate2d.py` | 2D slotted plate via shapely |
| `generators/bracket_cadquery.py` | reference bracket, CadQuery |
| `generators/bracket_build123d.py` | reference bracket, build123d |
| `generators/bracket_openscad.py` | reference bracket, solidpython2/OpenSCAD |
| `generators/__init__.py` | `GeneratorSpec` registry with lazy builder imports |
| `exchange/__init__.py` | the only writer of geometry: format dispatch, fixed destinations, skip-not-fail policy |
| `exchange/export2d.py` | SVG (drawsvg) and DXF (ezdxf) writers plus their read-back metrics |
| `exchange/export3d.py` | STEP/STL per kernel, `.scad` emission, OpenSCAD subprocess render, GLB via trimesh, mesh/STEP metrics |

Repository: `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`,
`config/artifacts.yaml`, `README.md`, `AGENTS.md` (rewritten), `tests/` (5
files), and five specs under `specifications/`.

## Implementation Facts

- **Environment.** `uv sync --extra all` installs 106 packages on Python
  3.12.13. Extras as planned; `pyyaml` added to the base dependencies (the
  OP-103 artifact config is YAML) — the only dependency beyond the plan sketch.
- **The reference part** is an L-bracket: base plate + web plate fused, four
  cylinders cut (two through the base on Z, two through the web on Y). It has a
  closed-form volume, so every backend is checked against arithmetic rather
  than against another backend. All three 3D backends construct it the same way
  (explicit cylinders, no selector-based hole cutting), which is what makes the
  comparison meaningful.
- **The 2D part** is a rounded plate with N slots and four corner holes, built
  with shapely boolean ops (erode/dilate for corner rounding, buffered segments
  for slot capsules) and exported to SVG + DXF with millimetre units.
- **Backend probing never imports a kernel**: `backends.status()` uses
  `importlib.util.find_spec`, so `cadctx info` and `cadctx generators` stay
  fast. Generator builders are imported lazily from the registry.
- **OpenSCAD** is fetched from GitHub releases by `cadctx fetch openscad` into
  `.tools/openscad/`, then invoked as `openscad -o <out.stl> <in.scad>`.
  Without the binary the backend still emits `.scad` and records STL/GLB as
  skipped (`degraded`), proven by a test that monkeypatches the resolver.

## Decisions Made During Development

- **OP-108 (raised and accepted 2026-08-11)** replaced the planned `out/`
  directory with the typed `.cache/` layout, the quiet-console contract, fixed
  geometry paths and the side-effect-free Python API. Folded into
  `specifications/workspace-layout/spec.md` and
  `specifications/agent-interface/spec.md`; the plan's OP table, OP-108 section
  and exit criteria were updated in the same pass.
- **Analytic reference over kernel cross-checks.** Each generator declares its
  exact volume/area from parameters alone. Backends are compared to that, not
  to each other, so a shared kernel bug cannot pass as agreement.
- **Skip, don't fail.** `exchange.export` records a per-format reason when a
  prerequisite is missing and returns `degraded`; only a genuine build error
  raises. This keeps a partial install (or a machine without OpenSCAD) green.
- **Five specs instead of the two anticipated.** The exchange-format and
  parameter-schema specs were planned; workspace-layout, agent-interface and
  external-binaries were folded out of the OP-103/OP-106/OP-108 rules, which
  are durable and not exchange-format concerns.

## Deviations From The Plan

- Artifacts land in `.cache/cad/` at fixed paths, not in `out/` (OP-108).
  `out/` remains git-ignored for anyone using it manually.
- Added `cadctx compare`, `cadctx paths` and `cadctx clean` beyond the planned
  `demo`/`fetch`. Cross-backend agreement was an exit criterion with no command
  behind it, and OP-106 requires every capability to be reachable through a
  documented command.
- `pyyaml` added to base dependencies (see above).

## Dependency Conflicts Resolved

Both worth knowing about — a plain `uv sync --extra all` fails without them:

- **CadQuery ↔ build123d OCP conflict.** `cadquery` requires `cadquery-ocp`
  (VTK-enabled), `build123d` requires `cadquery-ocp-novtk`. Both wheels install
  the same `OCP/` package, so whichever is written last wins and the other
  backend fails at import (`ImportError: cannot import name 'IVtkOCC_Shape'`).
  Resolved by pinning the VTK build everywhere:
  `override-dependencies = ["cadquery-ocp-novtk; sys_platform == 'never'"]` in
  `[tool.uv]`, plus `cadquery-ocp` in the `build123d` extra so that extra stays
  installable on its own.
- **numba backtracking.** Unconstrained, the resolver satisfied CadQuery's
  `numba` requirement with 0.53.1 — a source-only release that refuses to build
  on Python ≥3.10. Pinned with `numba>=0.61` in the `cadquery` extra.

## Bugs Found And Fixed During Proof

- `-f glb` alone produced nothing ("needs an STL to convert from"), because GLB
  is derived from a mesh. `exchange.export` now tessellates into a temporary
  directory when the caller did not also ask for the STL, so only the requested
  artifact lands in the workspace. Covered by
  `test_glb_alone_tessellates_without_leaving_an_stl`.
- `config/artifacts.yaml` initially pinned OpenSCAD tag `2021.01`; the actual
  GitHub tag is `openscad-2021.01`, which the fetch reported as a clean
  `GitHub API 404` result before being corrected.
- Rich wrapped long paths onto extra console lines under narrow terminals,
  breaking the one-fact-per-line contract; result rendering now prints with
  `soft_wrap=True`.

## Follow-Up Risks

- OpenSCAD is pinned to the 2021.01 stable release (the newest with GitHub
  release assets). Newer snapshots live on openscad.org and would use the
  `url` source kind already supported by the config schema.
- `drawsvg` remains the medium-confidence choice from OP-105. The SVG writer is
  one function (`export2d.write_svg`) emitting a single fill-rule path, so
  swapping it for hand-rolled SVG stays cheap.
- Mesh volumes are compared through trimesh only; no independent mesh validator
  is in the loop.
- `.tools/` provisioning is unverified on Linux and macOS — the AppImage and
  DMG entries in `config/artifacts.yaml` are declared but only the Windows path
  has been exercised.

## Commands That Matter

```bash
uv sync --extra all
uv run cadctx fetch openscad
uv run cadctx demo
uv run cadctx compare
uv run pytest
uv run ruff check .
```
