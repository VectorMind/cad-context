# Agent Guidance

Read this before doing anything in the repository. Binding contracts live in
`specifications/`; this is the operational summary.

## Start Here

Before any `uv` command, select an environment for the operating system running
the command. In a checkout shared with Windows, `.venv` belongs to Windows.
Linux/WSL agents must set a separate environment in every shell invocation:

```bash
export UV_PROJECT_ENVIRONMENT="$PWD/.cache/scratch/venv-linux"
```

Apply this before the startup commands below, installation, tests, lint, and
`cadcon web`; child processes must inherit it. An existing isolated Linux
validation environment may be reused. Never let Linux/WSL `uv` create, sync,
replace, or remove the shared `.venv`, even if it appears missing or broken.
Do not use `uv --active` to select a Windows environment from Linux. If `uv`
reports an incompatible environment, select a separate path instead of
recreating the other platform's environment. Keep environment overrides out of
shared `pyproject.toml` configuration so plain Windows `uv sync` stays unchanged.

Run these before touching code; each writes a result that can be re-read:

```bash
uv run cadcon info
uv run cadcon generators
uv run cadcon paths
```

Machine-readable answers are under `.cache/results/`; `last.json` is the newest.

## Two Surfaces

### `cadcon` produces artifacts

`cadcon` is the documented interface for humans and agents. A capability not
reachable through a documented command is not delivered. Add a command and its
README entry together. Use `--json` to parse output and `--quiet` for only the
result path.

The preview server is started only with `cadcon web`; do not serve with pnpm or
add a second long-running Python service.

### `cad_context.api` answers questions

The Python API returns data or native objects without files or console output:

```python
from cad_context import api

api.generators()
api.schema("plate2d")
api.metrics("bracket-build123d", width=120)
part = api.build("bracket-build123d").native
```

Throwaway scripts go in `.cache/scratch/`. Files require the CLI or an explicit
`cad_context.exchange.export(...)` call.

## Output Locations

Operational output stays under `.cache/`:

| Path | Contents |
| --- | --- |
| `.cache/results/` | bounded command JSON/Markdown summaries |
| `.cache/reports/` | tracebacks and long subprocess logs |
| `.cache/cad/` | built-in geometry at fixed paths |
| `.cache/scratch/`, `.cache/downloads/` | experiments and downloads |
| `.tools/` | provisioned external binaries |

An active project's working artifacts use fixed paths under
`.cache/projects/<project-id>/cad/<generator>/`, including measurements JSON.
Only explicit `cadcon project publish` and user-dated `project release` copy
consumer assets into shared storage; source/reference snapshots support recovery.
See specifications/project-publication/spec.md. Operational results remain local. Never write generated files
into `src/`, `plans/`, `specifications/`, or the repository root. Never commit
`.cache/`, `.tools/`, or generated project geometry.

Use `CAD_CONTEXT_CACHE` to redirect tests. Tests using a project fixture copy it
to `tmp_path`; redirecting the cache also redirects project working output.

Paths are stable and atomic. Do not introduce timestamps, hashes, or counters.
Use `--out-dir` only when several variants genuinely coexist. Keep the console
quiet; long content belongs in results or reports.

## Backend Focus

build123d is the single maintained 3D B-rep backend. Shapely owns 2D geometry,
trimesh owns mesh inspection/GLB bridging, and OpenSCAD remains an optional
project authoring toolchain for SCAD/Customizer or independent CSG delivery.
Do not add routine duplicate builders across backends.

Keep shape parameters, derived geometry, and analytic references independent of
the kernel. Native objects stay inside their generator/exporter boundary;
shared behavior is defined by STEP, STL, GLB, SVG, DXF, JSON, and SCAD.

An additional backend is a project-scoped, risk-triggered exception. Follow
`specifications/backend-policy/spec.md`; do not add it to the core dependency
surface without an accepted workbench-level plan.

## External Model Projects

New model-specific evidence, specs, plans, code, tests, and durable artifacts
belong in an external project folder. For supported build123d/Shapely/OpenSCAD
projects, working on a model requires no repository edit.

Initialize before selection:

```bash
uv run cadcon project init <path>
uv run cadcon project use <path>
```

Use global `--project <path>` for one command and `--no-project` to force
repository mode. Selecting a project trusts its Python code. The manifest,
loader, collision, and output contracts are in
`specifications/model-projects/spec.md`.

Portable project IDs and the default live in versioned `config/projects.yaml`.
Bind this machine's storage with `cadcon project root <name> <path>` (ignored
`config/projects.local.yaml`); inspect with `cadcon project list`. Selection also
accepts catalog IDs. `project clear` restores the catalog default; `--no-project`
bypasses it. Never commit machine-specific root bindings.
Automatic discovery requires a valid `project.yaml` with explicit `tool: cadcon`;
new `project init` scaffolds include it. Unrelated projects are not listed.

A project generator declares its module and `ShapeParams` subclass in
`project.yaml`; its module exposes `build(params) -> BuildResult`. Import kernels
inside `build`, write nothing from the builder, publish an analytic reference,
and ensure defaults produce a valid shape.

## Web App

`webapp/` is a preview surface, never a second geometry implementation.

- Ask `cadcon --json` for registry, schema, paths, and fresh artifacts.
- Built-in editable names live in `webapp/config/exposure.json`; project names
  live in `project.yaml`. Never copy ranges, units, or defaults there.
- One server process snapshots one active project. Restart to switch.
- Serve artifacts only from each registry entry's confined artifact root.
- A slow real generator gets a spinner, never an approximation.

## External Tools

Declare external binaries in `config/artifacts.yaml`; `cadcon fetch <name>` is
the only provisioning path. Missing tools degrade with explicit skipped formats
instead of crashing.

## Proof Obligations

Geometry proof means measurement:

- re-import STEP through build123d;
- load meshes and check volume, bounds, watertightness, vertices, and faces;
- re-read DXF/SVG/JSON and check structure, bounds, and units;
- compare exact 3D kernel/reference values at 1e-6 relative and tessellated,
  faceted, 2D-approximated, or explicitly approximate values at 1%;
- run `cadcon verify <generator>` for delivered generators;
- run `uv run pytest` and `uv run ruff check .`;
- run the web check, tests, and build when web surfaces change;
- record commands, expected/actual results, and gaps in the packet `test.md`.

## Git

The maintainer owns git operations. Do not run `git add`, `git commit`, `git
push`, or any other history-changing command. Leave finished work in the working
tree.

## Spec And Planning Workflow

Use `specifications/<slug>/spec.md` for durable requirements and
`plans/YYYY-MM/DD-<slug>/` for time-bounded work. Every packet has `plan.md` and
`test.md`. Create `implementation.md` only after implementation begins. Create
`survey.md` only when explicitly requested.

`plan.md` holds approved scope, milestones, dependencies, risks, exit criteria,
and stable open points (`OP-001`, etc.) with candidates, proposal, confidence,
and status. Do not silently collapse an unresolved choice.

`implementation.md` opens with a current filled/empty-block Progress line and
records changes, decisions, deviations, risks, and commands actually performed.
`test.md` records fixtures, commands, expected/actual results, and remaining
gaps. Update the packet whenever implementation changes its plan.

Fold every settled strategy, policy, or contract into the relevant durable spec
in the same pass. Repository `plans/` is for workbench changes; model SDD
documents live in their project folder.
