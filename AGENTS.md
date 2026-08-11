# Agent Guidance

Read this before doing anything in this repository. It tells you which surfaces
to use, where output is allowed to go, and what proof a change owes. The
binding contracts behind these rules live in [specifications/](specifications/);
this file is the operational summary.

## Start Here

Orient with three commands before touching code — each writes a result file you
can re-read instead of re-running:

```bash
uv run cadctx info          # backends installed, binaries resolved
uv run cadctx generators    # what can be generated, in which formats
uv run cadctx paths         # where everything is written
```

Machine-readable answers are in `.cache/results/<command>.json` under `data`.
`.cache/results/last.json` is always the most recent command.

## Two Surfaces, One Rule Each

### 1. The `cadctx` CLI — for anything that produces artifacts

`cadctx` is the single documented interface, for humans and agents alike. Every
capability is a subcommand documented in [README.md](README.md). **A capability
that is not reachable through a documented `cadctx` command is not delivered.**

- Adding a capability means adding a command *and* its README entry in the same
  pass.
- Do not create agent skills, plugin manifests, or tool-specific wrappers.
  Routing lives in `README.md`, this file, and `WORKFLOW.md` — plain files any
  agent can read.
- Use `--json` when you want to parse a command's output directly; use
  `--quiet` when you only need the result path.

Starting the preview web app is a command like any other: `cadctx web` installs
what is missing, starts the Astro server and prints the URL. Do not run `pnpm`
by hand to serve it, and do not add a second long-running Python process — the
app's pages call this CLI per request.

### 2. The Python API — for questions, never for artifacts

`cad_context.api` is available whenever you want numbers, a schema, or a live
kernel object. It is side-effect free: **no files, no console output, no
workspace writes.**

```python
from cad_context import api

api.generators()                              # registry as data
api.schema("plate2d")                         # parameter contract
api.metrics("bracket-cadquery", width=120)    # volume, area, bounds
api.compare(width=120)                        # cross-backend volumes
part = api.build("bracket-build123d").native  # live build123d object
```

Writing a throwaway script to explore is expected and encouraged. Put it in
`.cache/scratch/` and run it with `uv run python .cache/scratch/<name>.py`. If
that script needs artifacts on disk, either call the CLI or call
`cad_context.exchange.export(...)` explicitly — artifacts are never a side
effect of asking a question.

## Where Output Is Allowed To Go

Everything a run produces lands under the git-ignored `.cache/`:

| Path | Contents |
| --- | --- |
| `.cache/results/<command>.json` / `.md` | one small summary per command, overwritten each run |
| `.cache/reports/<command>.log` | long output (tracebacks, subprocess logs) |
| `.cache/cad/<generator>/<generator>.<ext>` | geometry, at fixed paths |
| `.cache/scratch/` | your throwaway scripts |
| `.cache/downloads/`, `.tools/` | fetched archives and unpacked binaries |

Rules that are not negotiable:

- Never write generated files into `src/`, `plans/`, `specifications/`, or the
  repository root. Never commit anything under `.cache/` or `.tools/`.
- **Geometry paths are fixed**, derived from the generator id alone. Do not add
  timestamps, hashes, or run counters to filenames: a viewer or browser tab
  holds one URL across a whole parameter-iteration session. Use `--out-dir`
  only when several variants must genuinely coexist.
- **Keep the console quiet.** Commands print a status line, a few facts and a
  result path. Anything long goes to `.cache/reports/` and is referenced by
  path. If you add output, add it to the result file, not to the terminal.
- Redirect the cache with `CAD_CONTEXT_CACHE` rather than writing into the real
  one from tests.

## Multitudes, Not Monoculture

This repository deliberately keeps multiple backends alive in parallel. When a
task could be solved by picking a winner, don't:

- Add capability to *each* relevant backend, or state plainly which ones you
  left out and why.
- Shared behavior is defined by exchange formats (STEP, STL, GLB, SVG, DXF),
  never by one backend's object model. Nothing outside a backend module may
  interpret that backend's native objects.
- The three bracket generators build the same part three ways on purpose. Keep
  their constructions equivalent so the cross-backend volume comparison stays
  meaningful.

## Adding A Generator

1. Put the parameter model in `src/cad_context/generators/models.py` using
   `number()` / `integer()` / `choice()`, with ranges, steps, units and
   descriptions on every field. Add the analytic formula for its volume or area
   in the same module — that value is the reference the exports are checked
   against, and it must not depend on any kernel.
2. Write the builder in `src/cad_context/generators/<name>.py` exposing
   `build(params) -> BuildResult`. It returns the native object plus metrics
   and **writes nothing**. Import the CAD kernel inside `build`, never at module
   level.
3. Register a `GeneratorSpec` in `src/cad_context/generators/__init__.py` with
   its id, kind, backend, formats and description.
4. Make sure `cad_context.exchange` can write every format you declared.
5. Add tests: the generator's measured output against the analytic reference,
   and an export round-trip that loads each file back.
6. Update the generator table and, if you added a command, the command
   reference in `README.md`.

Defaults alone must produce a valid shape — every generator has to be runnable
with no parameters.

## Touching The Web App

`webapp/` is a preview surface, not a second implementation. Two rules decide
most questions there (the rest are in `specifications/web-app/spec.md`):

- **Ask the CLI.** Anything about shapes — the registry, a schema, a fresh
  artifact — comes from a `cadctx … --json` subprocess in a server handler.
  Never re-derive geometry, parameter ranges or paths in TypeScript.
- **Expose a few knobs, deliberately.** `webapp/config/exposure.json` lists the
  parameter *names* each generator publishes; the endpoint rejects everything
  else. Adding a parameter to a generator does not put it on the API — adding
  its name there does. Never copy a range, unit or default into that file.

## Adding An External Tool

Declare it in `config/artifacts.yaml` (source, pinned tag, per-platform asset
pattern, install dir, executable path). Do not write new fetch code, and do not
document a manual install: `cadctx fetch <name>` provisions any declared tool.
A missing binary must degrade — emit what the Python side can, record the
skipped formats with a reason, report `degraded` — never crash.

## Proof Obligations

"It ran" is not proof. For geometry work, proof means measurement:

- load every export back (mesh volume, watertightness, bounds; STEP re-imported
  through a kernel; DXF re-read for polyline counts, bounds and units);
- compare against the analytic reference — 1e-6 relative for kernel volumes,
  1% for tessellated or faceted ones;
- run `uv run pytest` and `uv run ruff check .` before declaring done;
- record commands, expected and actual results in the packet's `test.md`.

## Git

The maintainer owns all git operations. Do not run `git add`, `git commit`,
`git push`, or any other history-changing command. Leave finished work in the
working tree.

## Spec And Planning Workflow

Use `specifications/` for stable, spec-driven requirements and `plans/` for
time-bounded planning packets.

- Store durable specifications under `specifications/<slug>/spec.md` when the
  work needs requirements that should outlive one implementation pass.
- Store planning work under `plans/YYYY-MM/DD-<slug>/`. Use a `YYYY-MM` month
  folder plus a `DD-<slug>` packet folder, where `DD` is the two-digit day the
  plan packet starts and `<slug>` is a short lowercase title.
- Every dated plan folder must contain `plan.md` and `test.md`.
- Create `implementation.md` only after implementation work has actually
  happened, to log facts really implemented. Never create it upfront as a
  stub during planning.
- Add `survey.md` only when the maintainer explicitly asks for a survey, not
  as a default step before planning.
- Keep `plan.md` focused on approved scope, milestones, dependencies, and exit
  criteria. Do not turn unreviewed survey notes into committed scope.
- Keep `implementation.md` as a running log of changes made, important
  decisions, deviations from the plan, and follow-up risks. Open it with a
  short **Progress** section (a filled/empty-block bar plus current phase, or
  `Done` when finished) and keep that bar current on every change.
- Keep `test.md` as proof of working behavior: commands run, fixtures used,
  expected and actual results, and any gaps that remain untested.

When a plan changes during implementation, update the packet folder so the
spec, plan, implementation notes, and test proof remain consistent.

Whenever the maintainer states a strategy, policy, contract, or wisdom-level
rule — or work settles such a decision — fold it into the relevant spec in the
same pass, not only into a plan.

## Repository-Specific Rules

- **Never collapse options prematurely.** This repository deliberately keeps
  multiple generator backends and multiple visualization paths alive side by
  side (e.g. CadQuery *and* build123d *and* OpenSCAD). When a plan needs a
  choice, record it as an open point with candidates, a proposal, a confidence
  level, and a status — do not silently pick one and drop the rest.
- Track open design decisions with stable IDs (`OP-001`, …), each carrying:
  the question, the candidate options, the current proposal, a confidence
  level (`high` / `medium` / `low`), and a status (`open` / `proposed` /
  `accepted` / `rejected`). Record the resolution only when the maintainer
  accepts it.
