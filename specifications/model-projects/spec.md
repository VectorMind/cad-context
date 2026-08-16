# Model Projects

## Purpose And Scope

A model project owns model-specific evidence, specifications, code, and durable
generated artifacts outside the `cad-context` repository. Adding or iterating a
model that uses the supported toolchain requires no repository edit.

One project is active at a time. Built-in generators remain available alongside
that project's generators.

## Selecting A Project

Resolution order is:

1. global `--project <path>` option;
2. `CAD_CONTEXT_PROJECT` environment variable;
3. the pointer written by `cadctx project use <path>` under the repository cache;
4. repository mode, with no project.

`--no-project` explicitly bypasses the environment and persisted pointer.
`cadctx project use` accepts only an initialized, valid project. Initialization
therefore precedes selection:

```text
cadctx project init <path>
cadctx project use <path>
```

`cadctx project init --dry-run <path>` reports the proposed scaffold without
writing. Initialization never overwrites an existing `project.yaml`.

## Manifest

The mandatory core is `project.yaml` plus `cad/`. `generators/`, `evidence/`,
and model SDD documents are conventional project-owned content. Manifest schema
version 1 is:

```yaml
version: 1
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
<project>/cad/<generator>/<generator>.<ext>
<project>/cad/<generator>/<generator>.measurements.json
```

Command results, reports, scratch files, downloads, and the active-project
pointer remain in the repository cache. Artifact writes use a same-directory
temporary file followed by replacement so a synced folder never exposes a
partially written artifact.

Tests copy checked-in fixture sources to a temporary project directory before
generating; redirected cache alone does not redirect project output.

## Web Process Lifetime

`cadctx web` snapshots the resolved project into the server process environment.
All CLI subprocesses spawned by that server use the same project. Changing the
persisted pointer does not switch a running server; restart the server to select
a different project. The UI groups project generators under the project name
and serves each generator only from its declared, confined artifact root.

## Project Documentation

Model-specific evidence, spec, plan, implementation log, test proof, and
handoff live in the project folder. Repository `plans/` is reserved for changes
to the workbench itself.
