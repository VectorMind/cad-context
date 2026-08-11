# Plan: CAD Generators Python Environment Bringup

Date: 2026-08-11
Status: Approved — all open points accepted by the maintainer 2026-08-11
(OP-103 and OP-106 with amendments recorded below). No code or
`pyproject.toml` exists yet by design; the dependency file is materialized
from the accepted decisions when Phase 1 starts.

## Problem Summary

The repository is empty. We need a Python environment that can generate 2D
vector geometry (SVG, DXF) and 3D shapes (B-rep and mesh) programmatically,
following the repository's standing rule: keep multiple generator backends
alive in parallel (CadQuery *and* build123d *and* OpenSCAD, etc.) behind
shared exchange-format contracts, instead of standardizing on one tool.

## Resolution Summary

All open points accepted by the maintainer 2026-08-11. OP-103 gained a
config-driven binary fetch script; OP-106 was strengthened into the
CLI-as-single-interface rule. One-glance state (details in the Open Points
section below):

| OP | Topic | Accepted Resolution | Confidence | Status |
| --- | --- | --- | --- | --- |
| OP-101 | Python version window | `>=3.11,<3.14`, pin 3.12 | high | accepted |
| OP-102 | B-rep backends | both CadQuery and build123d | high | accepted |
| OP-103 | OpenSCAD path | solidpython2 + fetch script pulling the binary from GitHub releases via an artifact config file; graceful degrade | medium | accepted |
| OP-104 | Mesh layer / booleans | trimesh + manifold3d; GLB bridge to web app | high | accepted |
| OP-105 | 2D vector stack | ezdxf + drawsvg + shapely | high (drawsvg medium) | accepted |
| OP-106 | Base runtime / CLI | numpy, pydantic, typer, rich; `cadctx` CLI as the single documented interface for humans *and* agents — no skills; includes a simple parametric demo shape exposing a few parameters (amendment from Plan 2, 2026-08-11) | high | accepted |
| OP-107 | Tooling | uv, ruff, pytest, evidence-engine conventions | high | accepted |

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
- Confidence: high. Status: **accepted 2026-08-11** as proposed.

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
- Confidence: high. Status: **accepted 2026-08-11** as proposed.

### OP-103 — CSG / OpenSCAD path

- Options:
  - **SolidPython2** (`solidpython2`): generates `.scad` source from Python;
    requires the OpenSCAD binary installed separately to render STL.
  - **Direct `.scad` text templates** (no dep): keep OpenSCAD purely as an
    external tool driven by subprocess.
  - **Skip OpenSCAD**, rely on manifold3d for CSG (see OP-104).
- Proposal: `solidpython2` in an `[openscad]` group, with the OpenSCAD
  binary documented as an external prerequisite and detected at runtime —
  degrade gracefully to emitting `.scad` only when the binary is absent.
- Confidence: medium — the binary dependency on Windows is the friction
  point; the graceful-degrade rule keeps CI green. Status: **accepted
  2026-08-11 with amendment** — the binary is not left as a manual install;
  it is provisioned by a config-driven fetch script (see amendment below).

**Amendment (accepted 2026-08-11): config-driven binary fetch.** External
binaries are managed as declared artifacts, not manual installs:

- A config file (`config/artifacts.yaml`) declares each external tool:
  GitHub repo (`openscad/openscad`), pinned release tag, an asset-name
  pattern per platform (e.g. `OpenSCAD-*-x86-64.zip` for Windows), an
  optional checksum, the install directory (`.tools/<name>/`), and the
  executable's relative path inside the unpacked asset.
- A fetch command (`cadctx fetch openscad`, or `cadctx fetch --all`) reads
  the config, downloads the matching asset from the repo's GitHub releases,
  verifies, unpacks into `.tools/`, and reports the resolved executable
  path. Runtime binary detection (above) checks `.tools/` first, then
  `PATH`.
- Feasibility, checked: OpenSCAD's official releases on
  `github.com/openscad/openscad` carry Windows x86-64 zip/installer assets,
  downloadable via the standard GitHub releases API — the scheme works
  as described. One caveat folded into the design: OpenSCAD *nightly/
  snapshot* builds are published on openscad.org rather than GitHub, so the
  config schema also allows a direct-URL source per entry as a fallback.
  The mechanism is generic — future external tools (e.g. XFoil, Plan 3)
  reuse the same config file and command.
- `.tools/` is git-ignored (derived artifact, per WORKFLOW.md).

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
- Confidence: high. Status: **accepted 2026-08-11** as proposed.

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
  SVG (revisit if templating proves simpler). Status: **accepted
  2026-08-11** as proposed.

### OP-106 — Base runtime and CLI shape

- Options: typer + rich (evidence-engine house style) vs argparse-only vs no
  CLI at all in this packet.
- Proposal: base deps `numpy`, `pydantic`, `typer`, `rich`; a minimal
  `cadctx` CLI with `cadctx demo <backend>` producing exports into `out/`.
  Pydantic models anticipate the Plan 2 parameter-schema contract.
- Confidence: high (raised from medium at acceptance — the CLI is no longer
  optional, it is the interface contract). Status: **accepted 2026-08-11
  with amendment** below.

**Amendment (accepted 2026-08-11): the CLI is the single interface for
humans *and* agents.** Every important capability is wrapped as a typer
subcommand (`cadctx demo`, `cadctx fetch`, generators as they land), and
every command is documented in `README.md` so that both a human and an
agent can drive the repo from documentation alone, in one prompt. The repo
deliberately targets **no agent skills**: instead of skill packages,
routing lives in plain documentation files (`README.md` command reference,
`AGENTS.md` pointers) that any agent reads and acts on directly. A
capability that is not reachable through a documented `cadctx` command is
not considered delivered. This is a durable, wisdom-level rule — fold it
into the spec at the Phase 5 spec fold.

**Amendment (accepted 2026-08-11, folded back from Plan 2's OP-203/OP-204
resolution): simple parametric demo.** Exposing a small set of parameters
on a shape is relevant to the CAD side generally, not only to the web app.
At least one demo shape must expose a few parameters through the pydantic
parameter-schema models and a documented `cadctx` command (e.g.
`cadctx demo bracket --param width=40`), serving as the first end-to-end
CAD-side example of the parameter-schema contract that the Plan 2 web app
consumes.

### OP-107 — Tooling

- Proposal: `uv` for env/lock, `ruff` + `pytest` in the `dev` group,
  `default-groups = ["dev"]`, line length 88, `testpaths = ["tests"]` —
  identical to evidence-engine conventions.
- Confidence: high. Status: **accepted 2026-08-11** as proposed.

## Proposed `pyproject.toml` Sketch

Reflects the accepted decisions; materialized as a real file when Phase 1
starts:

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

0. **Decisions.** Done 2026-08-11 — OP-101…OP-107 accepted (OP-103, OP-106
   amended); this plan updated to the accepted state.
1. **Environment.** `pyproject.toml`, `uv sync --extra all`, lockfile,
   `.gitignore` (`out/`, `.tools/`, `.venv/`, caches), package skeleton
   `src/cad_context/`; `config/artifacts.yaml` and `cadctx fetch` per the
   OP-103 amendment, proven by fetching OpenSCAD on Windows; `README.md`
   opens the command reference that OP-106 mandates, growing with every
   phase.
2. **2D smoke.** One parametric 2D part (e.g. a slotted plate) generated via
   shapely ops, exported to SVG (drawsvg) and DXF (ezdxf).
3. **3D smoke, one per backend.** The same reference part (e.g. a flanged
   bracket) in CadQuery, in build123d, and in OpenSCAD/SolidPython2; each
   exports STEP (where the kernel supports it) + STL; trimesh converts STL →
   GLB and reports volume/bounds. At least one demo shape exposes a few
   parameters via the pydantic parameter-schema models and the CLI (OP-106
   parametric-demo amendment).
4. **Proof.** pytest checks per export: file exists, loads back, measurable
   properties within tolerance; cross-backend volume agreement on the
   reference part. Record in `test.md`.
5. **Spec fold.** Write `specifications/exchange-formats/spec.md` from the
   accepted contracts, and record the OP-106 durable rule (documented
   `cadctx` CLI as the single human/agent interface, no skills, routing via
   README/AGENTS docs) plus the OP-103 artifact-management contract in the
   appropriate specs.

## Dependencies And Risks

- OCCT-based wheels (OCP) are large downloads; first `uv sync` is slow.
- OpenSCAD requires an external binary on Windows (OP-103 mitigations:
  `cadctx fetch` provisions it from GitHub releases; graceful degrade when
  absent; direct-URL config fallback for non-GitHub builds).
- manifold3d/trimesh version coupling occasionally lags; pin via lockfile.
- No dependency on Plans 2/3 — this packet unblocks both.

## Exit Criteria

- `uv sync --extra all` succeeds from a clean checkout on Windows.
- `cadctx fetch openscad` downloads, unpacks, and resolves a working
  OpenSCAD executable into `.tools/` from `config/artifacts.yaml` alone.
- `cadctx demo` (or pytest equivalent) produces SVG, DXF, STEP, STL, and GLB
  artifacts under `out/`.
- Every shipped `cadctx` command is documented in `README.md` with a usage
  line and example, sufficient for a human or an agent to run it from the
  documentation alone (OP-106).
- Cross-backend volume agreement on the reference part within 1%.
- `uv run pytest` and `uv run ruff check` clean.
- `test.md` records commands, expected, and actual results.
