# cad-context

A workbench for **programmatic CAD**: generate 2D vector geometry and 3D shapes
from Python, with several CAD backends kept alive side by side (CadQuery *and*
build123d *and* OpenSCAD *and* shapely), all speaking the same exchange
formats — STEP, STL, glTF/GLB, SVG, DXF.

Everything is driven by one command, `cadctx`. There is nothing else to learn.

---

## Ask An Agent To Do It

The whole repository is documented so that a coding agent can drive it from
these files alone. Paste any of these prompts:

> **"Generate the demo bracket in all three 3D backends and tell me whether
> their volumes agree."**
> The agent runs `cadctx demo` and `cadctx compare`, then reads the numbers out
> of `.cache/results/compare.json`.

> **"Make the bracket 120 mm wide with 10 mm holes and regenerate the GLB."**
> `cadctx generate bracket-cadquery -p width=120 -p hole_diameter=10`. The GLB
> lands at the same path as before, so a viewer tab just needs a refresh.

> **"What parameters does the 2D plate have, and what happens to its area if I
> double the slot count?"**
> The agent reads `cadctx schema plate2d`, then measures both variants through
> the Python API without writing any files.

> **"Start the shape viewer so I can play with the bracket parameters."**
> The agent runs `cadctx web` and hands back the URL. That one command installs
> the web app's dependencies if needed, checks which backends are ready, starts
> the Astro server, and prints where it is. Each page calls this same CLI per
> request — there is no second server to babysit.

> **"OpenSCAD isn't installed — set it up and prove it renders."**
> `cadctx fetch openscad` provisions the binary into `.tools/`, then
> `cadctx generate bracket-openscad` renders an STL through it.

> **"Add a generator for a mounting plate with a bolt circle, in build123d,
> with parameters for the bolt count and circle diameter."**
> The agent follows `AGENTS.md`, which spells out where generators live, how
> they register, and what proof a new one owes.

Agents get their rules from [AGENTS.md](AGENTS.md); the binding contracts live
in [specifications/](specifications/).

---

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11–3.13 (3.12 pinned in
`.python-version`).

```bash
uv sync --extra all       # all backends (large: OCCT wheels)
uv run cadctx info        # what is installed and what is missing
uv run cadctx fetch openscad   # provision the OpenSCAD binary into .tools/
```

Narrower installs work too: `--extra vector2d`, `--extra cadquery`,
`--extra build123d`, `--extra openscad`, `--extra mesh`. A backend that is not
installed is reported as unavailable and skipped — nothing breaks.

## Where Output Goes

Every run writes below a single git-ignored `.cache/` directory, and the
console stays quiet:

```text
.cache/results/    <command>.json + .md — the summary of each command
.cache/reports/    long logs that would otherwise flood the terminal
.cache/cad/        the geometry, at fixed paths that never change
.cache/scratch/    throwaway scripts
.tools/            fetched external binaries
```

Geometry paths are **stable**: `bracket-cadquery` always writes
`.cache/cad/bracket-cadquery/bracket-cadquery.glb`. Change a parameter,
regenerate, refresh your viewer — same URL, new shape.

---

## Preview In The Browser

```bash
uv run cadctx web
```

That is the whole setup. It installs the web app's dependencies on first run,
reports which backends are ready, starts the Astro server and prints its URL:

```text
ok web — serving http://127.0.0.1:4321/ (5/5 backends ready)
  url: http://127.0.0.1:4321/
  webapp: webapp
  backends_ready: shapely, cadquery, build123d, openscad, trimesh
  backends_missing: none
  generators: http://127.0.0.1:4321/api/generators.json
  note: stop with Ctrl-C; the dev server log is in the report file
  result: .cache/results/web.json
  report: .cache/reports/web.log
```

Open the URL, pick a generator, drag a slider: the shape regenerates and the
measured volume or area updates next to it.

**Both halves are running, and this is how they meet.** There is no separate
Python service — a page's backend is an Astro SSR handler that shells out to
this same CLI:

```text
browser ──POST /api/generate──▶ SSR handler ──▶ uv run cadctx generate … --json
   ▲                                                        │
   └──── GET /api/artifact/<generator>/<file> ◀── .cache/cad/ ◀┘
```

Dragging a slider never floods that pipeline: the client keeps **one request in
flight**, folds intermediate values into a single queued request, and drops any
response that a newer one has already superseded. A 40-step slider drag on the
build123d bracket produced 2 generations, not 40.

**Only a few parameters are exposed on purpose.** The generators keep their
full parameter models; the app publishes a short editable list per generator in
[`webapp/config/exposure.json`](webapp/config/exposure.json) — names only, with
ranges and units still read from the generator's schema:

```jsonc
"plate2d": { "editable": ["width", "slot_count", "slot_width"], "preview": "svg" }
```

Anything not listed is shown read-only at its default, and the endpoint rejects
it before spawning anything:

```bash
curl -s -X POST localhost:4321/api/generate -H 'content-type: application/json' \
  -d '{"generator":"plate2d","params":{"corner_radius":12},"seq":1}'
# {"seq":1,"error":"parameter \"corner_radius\" is not editable for plate2d
#  (editable: width, slot_count, slot_width)"}
```

Details in [webapp/README.md](webapp/README.md); the binding rules are in
[specifications/web-app/spec.md](specifications/web-app/spec.md).

---

## Command Reference

Global options: `--json` (print the result payload as JSON), `--quiet` (print
only the result-file path). Every command also writes
`.cache/results/<command>.json` and `.md`.

### `cadctx info`

Report the Python version, which backends are importable, and which external
binaries resolved.

```bash
uv run cadctx info
```

### `cadctx generators`

List every generator with its backend, kind (2d/3d), formats, and availability.

```bash
uv run cadctx generators
```

### `cadctx schema <generator>`

Print a generator's parameter contract — names, types, defaults, ranges, steps,
units. This is what a UI renders controls from.

```bash
uv run cadctx schema bracket-build123d
```

### `cadctx generate <generator> [-p key=value] [-f format]`

Generate one shape and export it to its fixed `.cache/cad/` path. Repeat `-p`
for each parameter and `-f` for each format; without `-f` every format the
generator supports is written. `--out-dir` writes elsewhere (for keeping
variants side by side), `--no-measure` skips loading the exports back.

```bash
uv run cadctx generate plate2d -p width=160 -p slot_count=5
uv run cadctx generate bracket-cadquery -p width=120 -p hole_diameter=10 -f glb
```

### `cadctx demo [--only <backend>] [-p key=value]`

Run every available generator with defaults (or with overrides), producing the
full set of artifacts. The quickest proof that an install works.

```bash
uv run cadctx demo
uv run cadctx demo --only build123d
```

### `cadctx compare [-p key=value] [--tolerance 0.01]`

Build the reference bracket on every installed 3D backend and compare their
volumes against the analytic value. `--no-meshes` compares kernel volumes only
(faster, but skips OpenSCAD, which has no in-process kernel).

```bash
uv run cadctx compare -p width=120
```

### `cadctx fetch [name] [--all] [--list] [--force]`

Provision external binaries declared in `config/artifacts.yaml` into `.tools/`.
Without arguments it lists what is declared and what is installed.

```bash
uv run cadctx fetch --list
uv run cadctx fetch openscad
```

### `cadctx web [--port 4321] [--host 127.0.0.1] [--open] [--no-install]`

Serve the preview web app in [`webapp/`](webapp/): a browser page per generator
with a few sliders, a 3D or 2D viewport, and live regeneration. Dependencies
are installed on first run; the dev server's own output goes to
`.cache/reports/web.log`, and the console prints only the URL. Stop it with
Ctrl-C.

```bash
uv run cadctx web
uv run cadctx web --port 4400 --open
```

### `cadctx paths`

Print the workspace layout and the fixed artifact path for every generator and
format — the map a viewer or web app resolves files from.

```bash
uv run cadctx paths
```

### `cadctx clean [--what all|results|reports|cad|scratch|downloads]`

Delete generated content under `.cache/`.

```bash
uv run cadctx clean --what cad
```

---

## Using It From Python

For measurements and experiments, call the API directly. It returns data and
live kernel objects, and it **writes nothing**:

```python
from cad_context import api

api.metrics("bracket-cadquery", width=120)   # volume, area, bounds
api.compare(width=120)                       # cross-backend volumes
part = api.build("bracket-build123d").native # a live build123d object
```

Files appear only when you ask for them — through `cadctx`, or explicitly via
`cad_context.exchange.export(...)`.

## What Ships Today

| Generator | Backend | Kind | Formats |
| --- | --- | --- | --- |
| `plate2d` | shapely | 2D | SVG, DXF |
| `bracket-cadquery` | CadQuery | 3D | STEP, STL, GLB |
| `bracket-build123d` | build123d | 3D | STEP, STL, GLB |
| `bracket-openscad` | OpenSCAD | 3D | SCAD, STL, GLB |

The three bracket generators build the *same* part three ways on purpose —
comparing backends is the point, not choosing one.

## Development

```bash
uv run pytest          # export round-trips, measured tolerances, CLI contract
uv run ruff check .    # lint

cd webapp && pnpm build   # the web app's production build
cd webapp && pnpm check   # TypeScript / astro check
cd webapp && pnpm test    # the regeneration scheduler's rules
```

Working agreements: [WORKFLOW.md](WORKFLOW.md) · plans in [plans/](plans/) ·
contracts in [specifications/](specifications/).
