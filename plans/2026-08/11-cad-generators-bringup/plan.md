# Plan: CAD Generators Python Environment Bringup

Date: 2026-08-11
Status: Planning — open points below need maintainer decisions before
implementation starts. No code or `pyproject.toml` exists yet by design; the
dependency file is materialized from OP resolutions, not before.

## Problem Summary

The repository is empty. We need a Python environment that can generate 2D
vector geometry (SVG, DXF) and 3D shapes (B-rep and mesh) programmatically,
following the repository's standing rule: keep multiple generator backends
alive in parallel (CadQuery *and* build123d *and* OpenSCAD, etc.) behind
shared exchange-format contracts, instead of standardizing on one tool.

## Goal And Objectives

- A `pyproject.toml` (uv-managed, hatchling build, mirroring the
  evidence-engine style: small base + granular optional-dependency groups +
  composed bundles) installing the selected backends.
- A thin `cad_context` package with one worked "hello shape" per backend
  proving each install actually generates and exports geometry.
- Exchange-format exports proving the bridge to the web app (Plan 2): every
  3D backend path ends in at least STL and glTF/GLB; every 2D path ends in
  SVG and/or DXF.
- A first `specifications/exchange-formats/spec.md` folded out of the
  accepted decisions.

## Scope And Non-Goals

In scope: dependency selection and installation, per-backend smoke
generators, export helpers, pytest proof.

Non-goals: the web app (Plan 2), the airfoil generator (Plan 3), any GUI,
constraint solvers, assemblies, drawings/dimensioning, CAM. No attempt to
unify backend object models — contracts live at the file-format boundary.

## Open Points

### OP-101 — Python version window

- Options: `>=3.11,<3.13` (safe overlap for OCCT-based stacks) vs `>=3.12`
  (newer, risks lagging wheels for CAD packages) vs `>=3.10` (widest, drags
  old baseline).
- Proposal: `>=3.11,<3.14`, pinned in `.python-version` to 3.12. CadQuery and
  build123d both ship wheels there; matches evidence-engine's 3.11+ floor.
- Confidence: high. Status: proposed.

### OP-102 — B-rep scripting backends (OCCT kernel)

- Options:
  - **CadQuery** (`cadquery`): mature, large user base, fluent selector API,
    STEP/STL/AMF export, CQ-editor ecosystem.
  - **build123d** (`build123d`): same OCCT kernel via OCP, more Pythonic
    (builder + algebra APIs), active development, direct interop with
    CadQuery workplanes is partial but both export STEP.
  - Only one of the two.
- Proposal: **install both** as separate optional groups (`[cadquery]`,
  `[build123d]`). They share the OCP/OCCT wheel so the marginal cost of the
  second is small, and the repo rule is multitudes. Same-shape examples in
  both APIs double as a living comparison.
- Confidence: high. Status: proposed.

### OP-103 — CSG / OpenSCAD path

- Options:
  - **SolidPython2** (`solidpython2`): generates `.scad` source from Python;
    requires the OpenSCAD binary installed separately to render STL.
  - **Direct `.scad` text templates** (no dep): keep OpenSCAD purely as an
    external tool driven by subprocess.
  - **Skip OpenSCAD**, rely on manifold3d for CSG (see OP-104).
- Proposal: `solidpython2` in an `[openscad]` group, with the OpenSCAD
  binary documented as an external prerequisite (winget/choco install) and
  detected at runtime — degrade gracefully to emitting `.scad` only when the
  binary is absent.
- Confidence: medium — the binary dependency on Windows is the friction
  point; the graceful-degrade rule keeps CI green. Status: proposed.

### OP-104 — Mesh layer and boolean engine

- Options:
  - **trimesh** + **manifold3d**: trimesh for load/inspect/repair/export of
    meshes (STL, glTF/GLB, 3MF, OBJ), manifold3d as a fast robust boolean
    backend trimesh can use.
  - trimesh alone (booleans via slower/optional backends).
  - Skip mesh layer entirely (export straight from OCCT tessellation).
- Proposal: **trimesh + manifold3d** in a `[mesh]` group. trimesh's GLB
  export is the designated bridge to the Plan 2 web viewer, and it gives
  measurable proof (volume, watertightness, bounds) for `test.md`.
- Confidence: high. Status: proposed.

### OP-105 — 2D vector stack

- Options:
  - **ezdxf** for DXF read/write — de facto standard, no real competitor.
  - SVG out: **drawsvg** (actively maintained) vs **svgwrite** (maintenance
    mode, frozen API) vs building SVG strings by hand.
  - 2D geometry ops: **shapely** (offsets, booleans on polygons) vs doing
    everything inside the CAD kernels' sketch modes.
- Proposal: `[vector2d]` group = **ezdxf + drawsvg + shapely**. shapely is
  cheap, battle-tested, and gives 2D booleans/offsets independent of any CAD
  kernel; svgwrite rejected for being in maintenance mode.
- Confidence: high for ezdxf and shapely; medium for drawsvg vs. hand-rolled
  SVG (revisit if templating proves simpler). Status: proposed.

### OP-106 — Base runtime and CLI shape

- Options: typer + rich (evidence-engine house style) vs argparse-only vs no
  CLI at all in this packet.
- Proposal: base deps `numpy`, `pydantic`, `typer`, `rich`; a minimal
  `cadctx` CLI with `cadctx demo <backend>` producing exports into `out/`.
  Pydantic models anticipate the Plan 2 parameter-schema contract.
- Confidence: medium — the CLI could be deferred to Plan 2 without loss;
  kept here because it is the cheapest proof harness. Status: proposed.

### OP-107 — Tooling

- Proposal: `uv` for env/lock, `ruff` + `pytest` in the `dev` group,
  `default-groups = ["dev"]`, line length 88, `testpaths = ["tests"]` —
  identical to evidence-engine conventions.
- Confidence: high. Status: proposed.

## Proposed `pyproject.toml` Sketch

Materialized only after OP-101…OP-107 are accepted; shown here so the review
argues about one concrete artifact:

```toml
[project]
name = "cad-context"
requires-python = ">=3.11,<3.14"
dependencies = ["numpy", "pydantic", "rich", "typer"]

[project.scripts]
cadctx = "cad_context.cli:main"

[project.optional-dependencies]
cadquery  = ["cadquery"]
build123d = ["build123d"]
openscad  = ["solidpython2"]        # OpenSCAD binary is an external prereq
mesh      = ["trimesh", "manifold3d"]
vector2d  = ["ezdxf", "drawsvg", "shapely"]
airfoil   = []                       # reserved — filled by Plan 3 decisions
all       = ["cad-context[cadquery,build123d,openscad,mesh,vector2d]"]

[dependency-groups]
dev = ["pytest", "ruff"]
```

## Implementation Phases

0. **Decisions.** Maintainer resolves OP-101…OP-107; sketch above updated to
   accepted state.
1. **Environment.** `pyproject.toml`, `uv sync --extra all`, lockfile,
   `.gitignore` (`out/`, `.venv/`, caches), package skeleton
   `src/cad_context/`.
2. **2D smoke.** One parametric 2D part (e.g. a slotted plate) generated via
   shapely ops, exported to SVG (drawsvg) and DXF (ezdxf).
3. **3D smoke, one per backend.** The same reference part (e.g. a flanged
   bracket) in CadQuery, in build123d, and in OpenSCAD/SolidPython2; each
   exports STEP (where the kernel supports it) + STL; trimesh converts STL →
   GLB and reports volume/bounds.
4. **Proof.** pytest checks per export: file exists, loads back, measurable
   properties within tolerance; cross-backend volume agreement on the
   reference part. Record in `test.md`.
5. **Spec fold.** Write `specifications/exchange-formats/spec.md` from the
   accepted contracts.

## Dependencies And Risks

- OCCT-based wheels (OCP) are large downloads; first `uv sync` is slow.
- OpenSCAD requires an external binary on Windows (OP-103 mitigation:
  graceful degrade).
- manifold3d/trimesh version coupling occasionally lags; pin via lockfile.
- No dependency on Plans 2/3 — this packet unblocks both.

## Exit Criteria

- `uv sync --extra all` succeeds from a clean checkout on Windows.
- `cadctx demo` (or pytest equivalent) produces SVG, DXF, STEP, STL, and GLB
  artifacts under `out/`.
- Cross-backend volume agreement on the reference part within 1%.
- `uv run pytest` and `uv run ruff check` clean.
- `test.md` records commands, expected, and actual results.
