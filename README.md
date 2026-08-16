# cad-context

A project-oriented programmatic CAD workbench. build123d is the maintained 3D
B-rep path, Shapely owns 2D geometry, trimesh proves mesh exports, and OpenSCAD
is available as an optional project toolchain. Models can live in external
project folders with their evidence, code, measurements, and stable artifacts.

## Install

```powershell
uv sync --extra default
```

The `default` extra contains build123d, mesh, and vector2d support. Add the
optional OpenSCAD authoring package and provision its external renderer with:

```powershell
uv sync --extra all
uv run cadctx fetch openscad
```

Missing optional tools degrade cleanly and are reported by `cadctx info`.

## Start Here

```powershell
uv run cadctx info
uv run cadctx generators
uv run cadctx paths
```

Every command writes a compact JSON and Markdown result below `.cache/results/`.
Use global `--json` for a machine-readable console response, `--quiet` for only
the result path, `--project <path>` for one command, or `--no-project` to bypass
the environment and persisted project pointer.

## External Model Projects

Initialize before selecting:

```powershell
uv run cadctx project init "C:\models\my-part"
uv run cadctx project use "C:\models\my-part"
uv run cadctx project info
```

Preview a scaffold without writing, and leave project mode, with:

```powershell
uv run cadctx project init "C:\models\my-part" --dry-run
uv run cadctx project clear
```

Selection precedence is `--project`, `CAD_CONTEXT_PROJECT`, the persisted
pointer, then repository mode. A project uses this core:

```text
my-part/
  project.yaml
  generators/
  evidence/
  cad/
```

Example manifest:

```yaml
version: 1
name: my-part
description: Example external model.
generators:
  - id: my-part
    title: My part
    kind: 3d
    backend: build123d
    module: generators.my_part
    params_model: MyPartParams
    formats: [step, stl, glb]
    family: my-part
    defaults: {}
exposure:
  my-part:
    editable: [width, height]
    preview: glb
```

The module exports a `ShapeParams` subclass and `build(params) -> BuildResult`.
Kernel imports stay inside `build`, builders write nothing, and analytic
references are computed independently of the kernel. Selecting a project trusts
its Python code. Supported project backends are build123d, Shapely, and optional
OpenSCAD; arbitrary project dependency environments are not part of the
workbench contract.

Built-in artifacts remain under `.cache/cad/`. Project artifacts and their
measurement summaries travel with the project:

```text
<project>/cad/<generator>/<generator>.<ext>
<project>/cad/<generator>/<generator>.measurements.json
```

## Generate And Verify

```powershell
uv run cadctx generate bracket-build123d -p width=120
uv run cadctx verify bracket-build123d -p width=120
uv run cadctx verify plate2d
```

`generate` writes every declared format unless repeated `--format/-f` options
select a subset. `--out-dir` deliberately keeps output elsewhere and
`--no-measure` skips round-trip measurements.

`verify` is format-aware. For 3D it checks the analytic reference, native
kernel volume, STEP re-import, mesh volume/bounds/watertightness, and declared
outputs. For 2D it checks analytic area plus SVG/DXF/JSON structure and units.
Missing optional external tools produce `degraded`; a failed required check is
an error.

Run all available generators with defaults:

```powershell
uv run cadctx demo
uv run cadctx demo --only build123d
```

## Preview Web App

```powershell
uv run cadctx web
uv run cadctx --project "C:\models\my-part" web
```

The command installs web dependencies when needed, starts Astro, and prints the
URL. The server snapshots one project for its lifetime; restart it after
switching projects. Its SSR handlers call `cadctx --json` for registry, schema,
generation, and paths. Project generators are grouped under their project name,
and each artifact is served only from its registry-declared root.

Only a curated subset of parameters is editable in the browser. Built-in names
live in `webapp/config/exposure.json`; project names live in `project.yaml`.
Ranges, units, steps, and defaults always come from the parameter model.

## Command Reference

### `cadctx info`

Report Python, supported backend packages, external binaries, and active
project.

### `cadctx generators`

List the merged built-in/project registry: backend, kind, formats, availability,
origin, project, exposure, and absolute artifact root.

### `cadctx schema <generator>`

Return the complete parameter, format, origin, exposure, and artifact contract.

### `cadctx generate <generator> [-p key=value] [-f format]`

Build, export, and by default re-read one generator's declared artifacts.

### `cadctx verify <generator> [-p key=value] [--tolerance 0.01]`

Apply the generator's analytic and format-aware proof obligations.

### `cadctx demo [--only <backend>] [-p key=value]`

Generate every available registry entry with defaults or applicable overrides.

### `cadctx project init <path> [--dry-run]`

Create the versioned manifest and conventional project directories without
overwriting an existing manifest.

### `cadctx project use <path>`

Validate and persist an initialized active project under `.cache/`.

### `cadctx project clear`

Remove the persisted pointer. It does not delete the project.

### `cadctx project info`

Report active project metadata without importing generator code.

### `cadctx fetch [<tool>|--all|--list]`

List or provision external binaries declared in `config/artifacts.yaml`.

### `cadctx web [--host 127.0.0.1] [--port 4321]`

Start the preview app, with `--install/--no-install` and optional `--open`.

### `cadctx paths`

Print repository cache paths, active project paths, and every stable artifact
destination.

### `cadctx clean [--what all|results|reports|cad|scratch|downloads]`

Delete selected generated repository-cache content. It never deletes a project
folder or the persisted project pointer.

## Python API

The in-memory API writes nothing:

```python
from cad_context import api

api.generators()
api.schema("plate2d")
api.defaults("bracket-build123d")
api.metrics("bracket-build123d", width=120)
part = api.build("bracket-build123d").native
api.paths()
api.backend_status()
```

Use the CLI, or call `cad_context.exchange.export(...)` explicitly, when files
are required.

## Built-In Generators

| id | family | backend | kind | formats |
| --- | --- | --- | --- | --- |
| `plate2d` | plate | Shapely | 2D | SVG, DXF |
| `airfoil` | airfoil | Shapely | 2D | SVG, DXF, JSON |
| `bracket-build123d` | bracket | build123d | 3D | STEP, STL, GLB |
| `wing-build123d` | wing | build123d | 3D | STEP, STL, GLB |

The backend and reconstruction policy is in
[`specifications/backend-policy/spec.md`](specifications/backend-policy/spec.md);
the external project contract is in
[`specifications/model-projects/spec.md`](specifications/model-projects/spec.md).

## Development Proof

```powershell
uv run pytest
uv run ruff check .
cd webapp
corepack pnpm check
corepack pnpm test
corepack pnpm build
```

Geometry proof is measurement, not appearance: STEP is imported again, meshes
are checked for watertightness/volume/bounds, and 2D formats are re-read for
structure and units.
