Current storage/navigation override (2026-11-08): specifications/project-publication/spec.md is authoritative. All generated project working state goes to local cache/projects/<id>; shared Drive gets explicit latest consumer publication, recovery/reference source and user-dated print releases. Historical project/cad output clauses below are superseded. Web projects use /projects and /projects/<id>, with separate local workbench.

# Model Projects

## Purpose And Scope

A model project owns model-specific evidence, specifications, code, and durable
generated artifacts outside the `cad-context` repository. Adding or iterating a
model that uses the supported toolchain requires no repository edit.

One project is active at a time. Built-in generators remain available alongside
that project's generators.

## Selecting A Project

Resolution order is:

1. global `--project <id-or-path>` option;
2. `CAD_CONTEXT_PROJECT` environment variable;
3. the pointer written by `cadcon project use <path>` under the repository cache;
4. `default` in versioned `config/projects.yaml`;
5. repository mode, with no project.

`--no-project` explicitly bypasses the environment, pointer, and catalog default.
`CAD_CONTEXT_NO_PROJECT=1` bypasses these fallbacks for child processes; an
explicit command selection still wins. `project clear` removes only the pointer,
returning to the configured default. Existing absolute-path pointers remain valid.
`cadcon project use` accepts only an initialized, valid project. Initialization
therefore precedes selection:

```text
cadcon project init <path>
cadcon project use <path>
```

`cadcon project init --dry-run <path>` reports the proposed scaffold without
writing. Initialization never overwrites an existing `project.yaml`.

## Portable Catalog And Discovery

`config/projects.yaml` is versioned configuration, schema version 1, with strict
fields `version`, optional `default`, `roots`, and `projects`. Each root has an
optional environment variable name (`env`) and a list of path `candidates`.
Each project ID maps to `root` and a confined relative POSIX `path`. The default
must name a registered ID; root references must exist. Unknown fields, absolute
project paths, dot segments, and resolved symlink escapes are errors.

Root resolution is the declared environment variable, then the root binding in
ignored `config/projects.local.yaml`, then an existing candidate. Candidate
paths expand `~`; multiple distinct existing candidates require an explicit
binding. No remote Drive API, drive-letter scan, or recursive filesystem search
is performed. `cadcon project root <name> <path>` validates the root name and
existing directory, then atomically persists its machine-specific binding under
`roots`. This is configuration, not cache, so cache cleanup preserves it.

Explicit selection and `CAD_CONTEXT_PROJECT` accept catalog IDs or paths.
`project use <id>` persists the ID, which resolves afresh on the next invocation.
Path-based selection remains supported. A missing default root/project is an
actionable error, never a silent fallback to another model. The delivered catalog
defaults to `animal-puzzle` at `shared-models/2026-10-24-animal-puzzle`.
`shared-models` uses `CADCON_SHARED_PROJECTS_ROOT` or a machine binding, with the
shared Drive folder as candidate. `models` uses `CADCON_PROJECTS_ROOT` or a
machine binding, with `~/My Drive/Projects/3d-models` and the old shared projects
folder as candidates; both existing requires an explicit binding. `airfoil-wing`
and `reference-parts` are registered under `models`.

`cadcon project list` reports all registered entries, their default flag, resolved
paths, availability, and manifest/root errors; it also discovers immediate child
directories containing a valid `project.yaml` with explicit `tool: cadcon` under
resolved roots. Missing markers, other tools, malformed YAML and invalid discovered
manifests are excluded. Explicitly registered invalid entries remain listed with
errors. Legacy manifests without a tool marker remain valid for explicit/catalog
selection, but must add the marker to participate in automatic discovery.
Discovery is confined
to those roots, deduplicates resolved paths, uses safe manifest parsing, and never
imports Python or writes project files. Discovered unregistered projects have no
catalog ID and can be selected by path. Only initialized projects are listed;
arbitrary model folders are not automatically initialized. Selecting a catalog
default carries the same local-code trust as selecting an explicit path. The web
server snapshots the resolved project as before; restart after selection changes.

## Manifest

The mandatory core is `project.yaml`; `cad/` is never a source directory. `generators/`, `evidence/`,
and model SDD documents are conventional project-owned content. Manifest schema
version 1 is:

```yaml
version: 1
tool: cadcon
name: example-part
description: Short purpose.
generators:
  - id: example-part
    title: Example part
    kind: 3d
    backend: build123d
    module: generators.example_part
    params_model: ExampleParams
    formats: [step, stl, glb]
    family: example-part
    defaults: {}
exposure:
  example-part:
    editable: [width, height]
    preview: glb
```

Generator ids are lowercase slugs containing letters, digits, and single
hyphens. Module names are dotted paths confined to the project. Supported
project backends are `build123d`, `shapely`, and optional `openscad`. Unknown
manifest fields, duplicate ids, invalid preview formats, and exposure entries
for unknown generators are errors.

Modules load lazily under a project-specific namespace, so listing paths or
project metadata does not execute generator code and sibling relative imports
do not collide with another project. Project imports do not create
`__pycache__` in the project folder.

## Trust Boundary

Selecting a project authorizes its Python generator modules to execute when a
schema, build, generate, or verify operation needs them. Manifests are parsed
with safe YAML loading, but Python generator code is trusted local code.

## Registry And Collisions

The active project's declarations merge with built-ins. A collision with a
built-in id or another project declaration stops discovery with an error naming
the conflicting id. No silent precedence or automatic renaming occurs.

Every registry row identifies its origin, project name, exposure, and absolute
artifact root. These values are the single contract consumed by the CLI and web
server.

## Output Routing

Built-in geometry remains under `.cache/cad/`. Project output uses stable paths:

```text
.cache/projects/<project-id>/cad/<generator>/<generator>.<ext>
.cache/projects/<project-id>/cad/<generator>/<generator>.measurements.json
```

Command results, reports, scratch files, downloads, and the active-project
pointer remain in the repository cache. Artifact writes use a same-directory
temporary file followed by replacement so a consumer never observes a
partially written artifact.

Tests copy checked-in fixture sources to a temporary project directory before
generating; redirected cache also redirects all project work outputs.

## Web Process Lifetime

`cadcon web` snapshots the resolved project into the server process environment.
All CLI subprocesses spawned by that server use the same project. Changing the
persisted pointer does not switch a running server; restart the server to select
a different project. The UI groups project generators under the project name
and serves each generator only from its declared, confined artifact root.

## Project Documentation

An optional `portfolio` declaration publishes an HTML entry and an explicit list
of presentation files, for example:

```yaml
portfolio:
  entry: PORTFOLIO.html
  files: [images/overview.svg, exports/review.step]
```

`cadcon --json project info` exposes the
entry and each declared file's availability without importing project code.
Paths use forward slashes, remain relative to the project, and cannot contain
empty, dot or parent components, backslashes or drive prefixes. Presentation
types are HTML, SVG, PNG/JPEG/WebP, PDF, STEP/STP, STL, GLB, 3MF, JSON and DXF.
Explicitly listed historical F3D archives may also be downloaded; this adds no
Fusion runtime or authoring support.
The web `/projects` page lists portable project IDs. `/projects/<id>` reads
only published consumer manifests/files; `/projects/<id>/workbench` reads local
working models and regenerated review evidence for the selected project.
`/project` redirects to the list. Source snapshot, GLB/reference and dated print
file downloads are allowlisted and realpath confined. HTML/SVG review files
remain sandboxed. See project-publication/spec.md for explicit lifecycle commands.

Model-specific source specs, plans, acceptance records and handoffs live in the durable source folder. Generated test/review evidence lives in local project cache. Repository `plans/` is reserved for changes
to the workbench itself.

## Format Declarations

Declared formats must match the generator's 2D/3D kind. `3mf` is supported only
for build123d generators and opts the generator into the single-piece contract
in `specifications/3mf-export/spec.md`. Separate pieces declare separate
generators; their 3MF files and measurement sidecars stay under their respective
project artifact directories.

## Consumer and regeneration declarations

Optional manifest fields: id (portable slug), publication {root,path} (shared catalog location), web_models {consumer-name: generator-id}, print_models {piece-name: generator-id}, web_files (confined source/cache image paths), rebuild_scripts (confined project Python paths). Model maps must reference generators declaring GLB/3MF respectively. Registry listing remains import-free. Source is durable outside cache; the catalog entry separately declares the publication location so published browsing and source restoration work without local source.
