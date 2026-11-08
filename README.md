# cad-context

A project-oriented programmatic CAD workbench. build123d is the maintained 3D
B-rep path, Shapely owns 2D geometry, trimesh proves mesh exports, and OpenSCAD
is available as an optional project toolchain. Models can live in external
project folders with their evidence, code, measurements, and stable artifacts.

## Install

```powershell
uv sync
```

This installs build123d, mesh, and vector2d support, including Shapely, for
both the CLI and web preview. The older `default`, `build123d`, `mesh`, and
`vector2d` extras remain accepted for compatibility. Add the optional OpenSCAD
authoring package and provision its external renderer with:

```powershell
uv sync --extra all
uv run cadcon fetch openscad
```

Missing optional tools degrade cleanly and are reported by `cadcon info`.

When using this checkout from both Windows and WSL, keep `.venv` for Windows.
Before running any `uv` commands in a WSL shell, select a Linux environment:

```bash
export UV_PROJECT_ENVIRONMENT="$PWD/.cache/scratch/venv-linux"
uv sync
```

Repeat the export in each new WSL shell. Virtual environments cannot be shared
between Windows and Linux; separate environments let both use the same source
checkout without replacing each other's packages or executable links.

## Start Here

```powershell
uv run cadcon info
uv run cadcon generators
uv run cadcon paths
```

Every command writes a compact JSON and Markdown result below `.cache/results/`.
Use global `--json` for a machine-readable console response, `--quiet` for only
the result path, `--project <path>` for one command, or `--no-project` to bypass
all project selection, including the configured default.

## External Model Projects

Initialize before selecting:

```powershell
uv run cadcon project init "C:\models\my-part"
uv run cadcon project use "C:\models\my-part"
uv run cadcon project info
```

Preview a scaffold without writing, and leave project mode, with:

```powershell
uv run cadcon project init "C:\models\my-part" --dry-run
uv run cadcon project clear
```

Selection precedence is `--project`, `CAD_CONTEXT_PROJECT`, the persisted
pointer, the catalog default, then repository mode. Options and the environment
accept either a catalog ID or a path. `project clear` removes the local selection
and returns to the catalog default; use `--no-project` for built-ins only.

The versioned [project catalog](config/projects.yaml) makes `animal-puzzle` the
default. It identifies the project by a root alias and relative folder, without
committing a machine-specific absolute path. Plain `uv run cadcon web` therefore
opens the animal puzzle, including its image gallery and geometry generators.

On each machine bind source and publication storage separately:

```powershell
uv run cadcon project root model-sources "C:\dev\VectorMind\model-projects"
uv run cadcon project root shared-models "G:\My Drive\Flatshare\3D Models Shared\projects"
uv run cadcon project list
uv run cadcon web
```

Bindings are saved in ignored config/projects.local.yaml, survive cache cleanup,
and may differ per machine. CADCON_SOURCES_ROOT and CADCON_SHARED_PROJECTS_ROOT
override these roots. Source is outside cache; shared storage receives only
explicit consumer publications and reference/source recovery snapshots.
There is no Google Drive API or automatic drive-letter scan: Drive must expose
the project files locally. Missing roots produce an actionable error.

The catalog includes `airfoil-wing` and `reference-parts`, preserved from the
workbench cache in the personal models root. Each owns generator source, original
cached exports, verified default geometry, and a portfolio. The animal puzzle
uses local `model-sources` and a separate `shared-models` publication root;
override that root with `CADCON_SHARED_PROJECTS_ROOT` or `project root shared-models
<path>`. It remains the default. On this machine, `models` is bound to
`~/My Drive/Projects/3d-models`.

`cadcon project list` lists registered projects (including unavailable ones) and
other immediate child folders with a valid `project.yaml` explicitly marked
`tool: cadcon`. Unrelated folders such as `characters-generation` are excluded,
even if they have their own `project.yaml`. It does not recurse, import
Python, initialize folders, or select newly found projects. Use
`cadcon project use animal-puzzle` for a registered ID, or `project use <path>`
for a discovered project. Add another `projects` entry to the catalog to give it
a shared ID. Project selection trusts its Python code. Restart the web server
after changing projects or root bindings.

A project uses this core:

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
tool: cadcon
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
measurement summaries remain in the local project cache:

```text
.cache/projects/<project-id>/cad/<generator>/<generator>.<ext>
.cache/projects/<project-id>/cad/<generator>/<generator>.measurements.json
```

## Generate And Verify

```powershell
uv run cadcon generate bracket-build123d -p width=120
uv run cadcon verify bracket-build123d -p width=120
uv run cadcon verify plate2d
```

`generate` writes every declared format unless repeated `--format/-f` options
select a subset. `--out-dir` deliberately keeps output elsewhere and
`--no-measure` skips round-trip measurements.

`verify` is format-aware. For 3D it checks the analytic reference, native
kernel volume, STEP re-import, mesh volume/bounds/watertightness, and declared
outputs. For 2D it checks analytic area plus SVG/DXF/JSON structure and units.
Missing optional external tools produce `degraded`; a failed required check is
an error.

Geometry-only 3MF is available for a single build123d solid:

```bash
uv run cadcon generate bracket-build123d -f 3mf
uv run cadcon verify bracket-build123d -f 3mf
```

Declare `formats: [3mf]` (or include it beside STEP/STL/GLB) in a build123d
project generator to make it part of default generation and verification.
Built-in defaults stay STEP/STL/GLB. Both commands accept repeated `-f` options
for explicit format selection. `cadcon --json info` lists supported exchange
formats.

3MF uses explicit millimetres, Z-up, and native tessellation at 0.01 mm / 0.1 rad.
Each artifact contains one printable mesh and one build item, with no slicer
profile. Multiple solids are rejected; separate physical pieces use separate
project generators. Package references, instance transforms, mesh topology,
signed volume and bounds are checked on the actual 3MF. Invalid geometry fails
before replacing a previous file, including with `--no-measure`. Missing runtime
support is reported as a skip during generation; verification fails when a
requested/declared required artifact is missing. Optional OpenSCAD rendering
continues to produce `degraded` when its external tool is absent.

Run all available generators with defaults:

```powershell
uv run cadcon demo
uv run cadcon demo --only build123d
```

## Preview Web App

```powershell
uv run cadcon web
uv run cadcon --project "C:\models\my-part" web
```

The command installs web dependencies when needed, starts Astro, and prints the
URL. The server snapshots one project for its lifetime; restart it after
switching projects. Its SSR handlers call `cadcon --json` for registry, schema,
generation, and paths. Project generators are grouped under their project name,
and each artifact is served only from its registry-declared root.

Only a curated subset of parameters is editable in the browser. Built-in names
live in `webapp/config/exposure.json`; project names live in `project.yaml`.
Ranges, units, steps, and defaults always come from the parameter model.

## Command Reference

### `cadcon info`

Report Python, supported backend packages, external binaries, and active
project.

### `cadcon generators`

List the merged built-in/project registry: backend, kind, formats, availability,
origin, project, exposure, and absolute artifact root.

### `cadcon schema <generator>`

Return the complete parameter, format, origin, exposure, and artifact contract.

### `cadcon generate <generator> [-p key=value] [-f format]`

Build, export, and by default re-read one generator's declared artifacts.

### `cadcon verify <generator> [-p key=value] [-f format] [--tolerance 0.01]`

Apply the generator's analytic and format-aware proof obligations.

### `cadcon demo [--only <backend>] [-p key=value]`

Generate every available registry entry with defaults or applicable overrides.

### `cadcon project init <path> [--dry-run]`

Create the versioned manifest and conventional project directories without
overwriting an existing manifest.

### `cadcon project use <id-or-path>`

Validate and persist an initialized active project under `.cache/`. Catalog IDs
remain IDs in the pointer and resolve against the current machine's root.

### `cadcon project root <name> <path>`

Bind a catalog root to this machine's existing folder in ignored local config.

### `cadcon project list`

Report registered and discovered projects, resolved paths, availability, and the
configured default. Use `--json` for the complete list and individual errors.

### `cadcon project clear`

Remove the persisted pointer, restoring the catalog default. It does not delete
the project. Use global `--no-project` to bypass the default as well.

### `cadcon project info`

Report active project metadata without importing generator code.

Project builders may select finer mesh export quality without changing geometry:

```python
from cad_context.types import BuildResult, Tessellation

return BuildResult(
    generator="my-print-part", backend="build123d", kind="3d",
    params=params.model_dump(), native=part,
    tessellation=Tessellation(linear_deflection=0.0001, angular_deflection=0.02),
)
```

The normal `generate` and `verify` commands use that profile for STL, GLB and
3MF and record it in project measurements. Fine profiles can produce large
files; a separate print generator can retain a lighter preview. Omitted quality
uses the existing 0.01 / 0.1 deflections. Native STEP geometry is unchanged.
Generators may opt into build123d's Mesher STL writer with
`Tessellation(stl_writer="mesher")` when fine-feature export measurements require
it. `cadcon generate` and `verify` use that selection for STL and derived GLB;
the default writer remains unchanged. No post-export mesh repair is performed.
An optional `portfolio: {entry: PORTFOLIO.html, files: [images/overview.svg]}`
in `project.yaml` exposes explicitly listed presentation files and availability
in the JSON result for compatibility. Open `/projects` to list projects,
`/projects/<id>` for published models/releases, and `/projects/<id>/workbench`
for local cache models and regenerated review evidence. `/project` redirects
to the project list. Published and local file routes are separately allowlisted
and realpath-confined; generated downloads remain confined to local artifact roots.

### `cadcon fetch [<tool>|--all|--list]`

List or provision external binaries declared in `config/artifacts.yaml`.

### `cadcon web [--host 127.0.0.1] [--port 4321]`

Start the preview app, with `--install/--no-install` and optional `--open`.

### `cadcon paths`

Print repository cache paths, active project paths, and every stable artifact
destination.

### `cadcon clean [--what all|results|reports|cad|scratch|downloads]`

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

The GLB exporter preserves explicitly assigned native assembly colours as
separate solid PBR meshes, including parent placement. The web viewer keeps
those authored materials; ordinary uncoloured CAD previews keep the default
surface. Preview colours do not define slicer filament profiles.

## Project working files, publication and recovery

All generated project geometry now lives under `.cache/projects/<id>/cad/`. Keep durable model code, inputs, specs and original references outside cache. Project source and Drive publication roots are separately catalogued; bind this machine with `cadcon project root model-sources <parent>` and `cadcon project root shared-models <drive-projects-parent>`.

```powershell
uv run cadcon project list
uv run cadcon --project animal-puzzle project rebuild
uv run cadcon project publish animal-puzzle
uv run cadcon project snapshot animal-puzzle
uv run cadcon project present animal-puzzle
uv run cadcon project restore animal-puzzle <new-source-folder>
# Only on explicit user request:
uv run cadcon project release animal-puzzle YYYY-MM-DD
uv run cadcon project freeze animal-puzzle YYYY-MM-DD
```

`rebuild` recreates/validates all declared model exports and recovery/proof scripts locally. `publish` exports only declared latest GLB/reference views and the portable source/reference snapshot, never a print release. `snapshot` refreshes source recovery without publishing geometry. `restore` validates checksums and refuses to overwrite local edits. After cache loss, select the durable source and rebuild; on a new machine restore/bind source first. Exact mesh bytes need not match, but topology and measured geometry must pass verification.

Open `/projects` for the project list, `/projects/animal-puzzle` for published models and dated print releases, and `/projects/animal-puzzle/workbench` for local mutable working models. Published files remain usable with an empty cache or missing local source. Legacy `/project` redirects to the list. Dated print folders contain only explicit individual-piece generic 3MF packages plus a manifest. No `current` folder or automatic new release. Git initialization/commits remain maintainer-owned; Drive source snapshots provide continuation until source history is published.

To resume after a proof-script-only fix without redoing unchanged exports, use `cadcon --project animal-puzzle project rebuild --reuse-exports`. The saved verified source/output checkpoint must still match. A clean-cache rebuild always regenerates everything. For published browsing without local project source, start `cadcon --no-project web`.

Dated print downloads can be historical even when the viewer shows the latest model. `cadcon project view <id>` reports each release's source relationship to the published viewer snapshot; the project page warns about untracked historical exports or different source versions. New releases record the source identity and each file's generator. A filename revision, date or passing mesh check does not establish current appearance approval. Review the active generator mapping and approval record before selecting files for a release.

Create a new dated or labelled print version only when the user requests or confirms it. Model generation does not imply a new release. User-authorized consolidation may update an existing date; preserve all user-added G-code/slicer files and record their provenance separately from generated geometry.

For visual development pages, define `presentation.yaml` in the model source and run `cadcon project present <id>`. It publishes captioned image stages from explicitly declared source/cache paths to `web/gallery/latest`, preserving all current GLB/3MF geometry and release provenance. The definition is included in recovery snapshots and their conflict checks; presentation edits do not invalidate geometry verification. Cache images must be recreated with `project rebuild` if missing. Each stage has an `id`, `title`, `description`, `state` (`reference`, `history`, `approved` or `review`) and `assets` with `path`, `location` (`source` or `cache`), `title`, `caption` and optional `wide`/`state`.
