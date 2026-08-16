# Plan: Default Library And Project Folder Workflow

Packet: `plans/2026-08/16-default-lib-folder/`
Status: planning closed — two maintainer decision passes on 2026-08-16
resolved all open points (OP-501…OP-516). Ready for implementation;
implementation has not started.
Basis: the cache-barriere experience and its handoff
(`…\15-cache-barriere\handoff.md`, external), which recorded OP-408
(default-backend policy) as proposed.

## Problem Summary

Two structural problems surfaced during the cache-barriere family work:

1. **Backend multiplicity has a real cost.** Implementing every model in
   CadQuery, build123d, and OpenSCAD tripled builder code for identical shared
   geometry, while CadQuery and build123d share the OCCT kernel anyway (no real
   independence) and OpenSCAD needs an external binary. The dependency side is
   equally heavy: CadQuery and build123d pin *conflicting* OCP wheels
   (`cadquery-ocp` with VTK vs `cadquery-ocp-novtk`), currently held together
   by an `override-dependencies` hack in `pyproject.toml`, plus a numba floor
   pin for CadQuery alone. The repository converges on **one well functioning
   default 3D library** and stops maintaining code not actively intended to be
   used.

2. **New models require editing this repository.** Every new part today means
   touching `src/cad_context/generators/`, the registry, exposure config, and
   the repo test suite. The cache-barriere model was in fact developed *outside*
   this repo (its packet lives in a OneDrive folder) and left zero trace in
   `src/`. We adopt a **project folder workflow**: a user-supplied folder
   (given on the first prompt or via an environment variable) carries
   everything specific to a model family — evidence, spec, parameters,
   optional generator code — and receives all generated artifacts, with the
   web app serving models straight from there. Working on a project must never
   require a change to this repo that would need a git commit.

Example project folder for later validation (no generation effort in this
packet): `C:\Users\wassi\OneDrive\Partage Wassim Mezri\cache-barriere` —
currently raw evidence only (`dimensions.md`, photos, sketch).

## Maintainer Decision Pass (2026-08-16)

The maintainer accepted the direction and **strengthened** the cleanup side:
variant backend code is not frozen as reference families (the original
OP-502 proposal) — it is **dropped**. Variants survive only as specification
content: the rationale for what was kept, and enough regeneration information
to rebuild a variant easily if ever needed. Previous plan packets remain the
historical record. This supersedes the repository's "multitudes, not
monoculture" rule in its strong form; the durable part of that rule —
contracts over exchange formats, never one backend's object model — remains
binding.

A second pass the same day resolved the residual points: project knob
exposure lives in `project.yaml` (OP-514); CadQuery is removed entirely while
OpenSCAD stays live as an opt-in export toolchain behind its flag/extra, with
rationale and recovery information in README and/or spec (OP-515); the family
`compare` sweep is replaced by a renamed single-generator proof command
(OP-516).

## Resolution Summary

One-glance state of every open point. All sixteen are resolved; nothing
gates implementation.

| OP | Topic | Resolution / proposal | Confidence | Status |
| --- | --- | --- | --- | --- |
| OP-501 | Default 3D backend | build123d is the default and only maintained 3D backend; OpenSCAD opt-in | high | accepted |
| OP-502 | Fate of existing backend variants | Drop all variant code (`bracket-cadquery`, `bracket-openscad`, `wing-cadquery`); document rationale + regeneration recipe in spec only | high | accepted |
| OP-503 | Dependency layout | Lean `default` extra as the documented install; unused code/deps are not kept — see OP-515 for exact removal scope | high | accepted |
| OP-504 | Preferred-implementation mechanism | Not built — obsolete once each family has a single implementation; regeneration info lives in spec | high | accepted (mechanism dropped) |
| OP-505 | Validation level per model | No per-model level field; variants exist only in spec and previous plans; routine validation = analytic reference + export round-trip | high | accepted |
| OP-506 | Project folder designation | Layered: `--project` flag > `CAD_CONTEXT_PROJECT` env > persisted pointer (`cadctx project use`) > repo mode | high | accepted |
| OP-507 | Project folder layout | Minimal core (`project.yaml` + `cad/`); `evidence/`, `generators/`, docs as conventions; `cadctx project init` scaffolds | high | accepted |
| OP-508 | Per-project Python code | Execute code from the project folder in place, via the repo's uv venv; `.cache` staging documented as fallback | high | accepted |
| OP-509 | Output routing | Split: geometry + per-model measurements → project folder; command results/reports/scratch stay in repo `.cache/` | high | accepted |
| OP-510 | Web serving from project | Per-generator artifact roots from the registry payload; web UI lists and serves project models; memoization invalidatable | high | accepted |
| OP-511 | Naming/collisions | Best effort, no forced namespacing: user avoids conflicts; any collision stops with a clear conflict message | high | accepted |
| OP-512 | Model SDD docs location | In the project folder; repo `plans/` reserved for cad-context itself | high | accepted |
| OP-513 | Spec capture | Everything decided here is folded into specs in the same implementation pass | high | accepted |
| OP-514 | Knob exposure for project generators | `exposure` block in `project.yaml`, merged with repo `exposure.json` at request time | high | accepted |
| OP-515 | Exact removal scope (deps, probes, OpenSCAD path) | CadQuery removed entirely (code, extra, pins, override hack, probe); OpenSCAD stays live as opt-in export toolchain behind its flag/extra; rationale + easy-recovery info in README and/or spec | high | accepted |
| OP-516 | Fate of `cadctx compare` | Repurposed as single-generator proof command **and renamed** — proposed name `cadctx verify`; family sweep dropped | high | accepted |

## Goal And Objectives

**Goal:** make cad-context a stable, generic workbench specialized on one
default 3D library, while every new model lives in its own external project
folder that needs no edits to this repository.

Objectives:

1. Land the accepted backend policy: build123d only in code, variants
   documented-not-maintained, dependency surface reduced accordingly.
2. Capture regeneration recipes and rationale in a durable spec *before*
   deleting variant code, so a variant can be rebuilt easily when a checkpoint
   or deliverable demands it.
3. Deliver the project-folder contract: designation, layout, in-place code
   loading, split output routing, and web serving.
4. Keep per-model SDD documentation in the project folder; repo `plans/` is
   for the workbench itself.
5. Keep everything reachable through documented `cadctx` commands.

## Scope And Non-Goals

In scope:

- Deletion of variant generator code, their registry entries, exposure
  entries, and tests — after the spec captures recipes and rationale.
- Registry/CLI/webapp/pyproject changes implementing the accepted OPs.
- New durable specs (backend policy, model projects) and updates to
  `AGENTS.md`, `WORKFLOW.md`, `README.md`, and affected existing specs —
  including rewriting the "multitudes" sections to the narrowed form.
- A fixture project under tests (cache redirected) proving loading, routing,
  and collision behavior.
- Dry validation against the real `cache-barriere` folder (resolution +
  listing only).

Non-goals:

- **No model generation for cache-barriere in this packet.**
- **No warm-worker/latency work** (OP-204 carry-forward stays separate; this
  plan must not make latency worse).
- No dependency-file edits before implementation starts; pyproject changes
  land in phase 2, after the specs capture the recipes (phase 1).
- No multi-project simultaneous serving; one active project at a time.

## Open Points

### Cluster A — one default 3D library

#### OP-501 — Default 3D backend policy

- **Question:** which backend is the default for new models?
- **Candidates considered:** all-three-per-model (status quo); build123d
  default with risk-triggered additions (handoff OP-408); CadQuery default;
  per-model free choice.
- **Resolution (2026-08-16): accepted — build123d.** OpenSCAD remains
  *opt-in* (toolchain available for `.scad`/Customizer delivery or independent
  CSG evidence when a project needs it). CadQuery is not retained as a
  maintained option; see OP-502/OP-515.
- **Confidence:** high. **Status:** accepted.

#### OP-502 — Fate of the existing backend variants

- **Question:** what happens to `bracket-cadquery`, `bracket-openscad`,
  `wing-cadquery`?
- **Candidates considered:** delete; keep extending; freeze as reference
  families (original proposal).
- **Resolution (2026-08-16): accepted as modified — drop the code.** The
  spec documents, for historical reference: why build123d was kept (rationale
  from the handoff's measured comparison), and what allows easy regeneration
  of a variant if needed — the shared-geometry contract (`models.py` computes
  everything backend-independent), the builder contract
  (`build(params) -> BuildResult`, kernel imports inside `build`), the
  export/measurement obligations, and pointers to the previous plan packets
  where the deleted implementations are described. Code is deleted to save
  maintenance effort; no frozen reference families.
- **Consequence:** the repo test suite and `webapp/config/exposure.json` lose
  the variant entries in the same pass; the bracket and wing families collapse
  to single implementations.
- **Confidence:** high. **Status:** accepted.

#### OP-503 — Dependency layout

- **Question:** how do install extras reflect the default?
- **Resolution (2026-08-16): accepted —** lean `default` extra
  (build123d + mesh + vector2d) as the documented day-one install, and the
  general rule is recorded: **code and dependencies not actively intended to
  be used are not kept.** The exact removal scope (CadQuery extra, OCP
  override hack, numba pin, backend probes, OpenSCAD extra) is pinned down in
  OP-515 before pyproject is touched.
- **Confidence:** high. **Status:** accepted.

#### OP-504 — Preferred-implementation mechanism

- **Question:** how would CLI/web know a family's default member?
- **Resolution (2026-08-16): mechanism dropped.** With variants removed
  (OP-502) every family has exactly one implementation, so a family→default
  map, `--all-backends` sweeps, and web-app backend selectors are obsolete.
  Regeneration information lives in the spec, and the spec also records the
  rationale for what was kept.
- **Confidence:** high. **Status:** accepted (as: not needed).

#### OP-505 — Validation level per model

- **Question:** how is required validation depth recorded?
- **Resolution (2026-08-16): no level field.** Variants exist only in spec
  and previous plans, so `dual-check`/`reference-family` are not routine
  options. Routine proof for every model remains: analytic reference
  comparison (1e-6 relative for kernel volumes, 1% for meshes) plus export
  round-trip (re-import STEP, measure mesh volume/bounds/watertightness).
  When a genuine independence need arises, a variant is regenerated from the
  spec recipe as a one-off checkpoint, recorded in that project's packet.
- **Confidence:** high. **Status:** accepted.

### Cluster B — project folder workflow

#### OP-506 — How the project folder is designated

- **Resolution (2026-08-16): accepted —** layered resolution:
  `--project` flag > `CAD_CONTEXT_PROJECT` env var > persisted pointer
  written by `cadctx project use <path>` (stored under `.cache/`) > none
  (repo-local mode, exactly today's behavior). `cadctx paths` and
  `cadctx info` always print the active project; `cadctx project clear`
  drops the pointer.
- **Confidence:** high. **Status:** accepted.

#### OP-507 — Project folder layout contract

- **Resolution (2026-08-16): accepted —** minimal mandatory core:
  `project.yaml` (name, description, model/generator declarations, defaults)
  and `cad/` for artifacts; conventional optional directories `evidence/`,
  `generators/`, and the model's SDD documents (OP-512). An evidence-only
  folder (like the real cache-barriere folder today) is a valid starting
  state; `cadctx project init` scaffolds the core into it.
- **Confidence:** high. **Status:** accepted.

#### OP-508 — Per-project Python generator code

- **Resolution (2026-08-16): accepted —** generator code executes **from the
  project folder in place**: modules under `<project>/generators/` declared in
  `project.yaml`, loaded with importlib machinery, following the exact repo
  generator contract (params model via `number()`/`integer()`/`choice()`,
  `build(params) -> BuildResult`, kernel imports inside `build`, analytic
  reference in shared math, builders write nothing). The interpreter and
  environment are always the repo's uv venv, so execution stays within this
  workspace's toolchain. The `.cache/projects/<name>/` staging copy is
  specified as the documented fallback to switch on only if OneDrive sync
  latency or file locking is observed. Trust boundary stated in the spec:
  pointing `cadctx` at a project folder means executing that folder's code.
- **Confidence:** high. **Status:** accepted.

#### OP-509 — Output routing in project mode

- **Resolution (2026-08-16): accepted —** split routing. Geometry
  (`<project>/cad/<generator>/<generator>.<ext>`, same fixed-path rule as
  today) and per-model measurement summaries go to the project folder — what
  the user keeps travels with the project. Command results, reports, scratch,
  and downloads stay in repo `.cache/` — operational noise never lands in a
  synced user folder. `workspace.layout()` grows project-aware entries so all
  consumers keep resolving paths from the contract.
- **Confidence:** high. **Status:** accepted.

#### OP-510 — Web app serving from the project folder

- **Resolution (2026-08-16): accepted —** the web UI lists and serves
  project models. Each registry entry carries its artifact root (repo cache
  for built-ins, project `cad/` for project generators); the artifact route
  resolves and confines per generator. The server's registry/paths/schema
  memoization becomes invalidatable (dev-mode TTL or refresh hook), or a
  project switch demands a restart *loudly* — silent staleness cost real
  debugging time on cache-barriere.
- **Confidence:** high. **Status:** accepted.

#### OP-511 — Project generator naming and collisions

- **Resolution (2026-08-16): accepted as modified — best effort, no forced
  namespacing.** Project generator ids are used as declared in
  `project.yaml`; the user is responsible for avoiding conflicts. On any
  collision (with a built-in id or within the project) loading **stops with a
  clear conflict message** naming both sides — no auto-renaming, no silent
  precedence. The web UI still groups project generators under the project
  heading.
- **Confidence:** high. **Status:** accepted.

#### OP-512 — Where a model's SDD documents live

- **Resolution (2026-08-16): accepted —** in the project folder. Someone
  working on a project must never need to edit the code-repo workspace in a
  way that requires a git commit. Repo `plans/` is reserved for work on
  cad-context itself; the model-projects spec documents the recommended
  per-model document set (evidence inventory → spec → plan → test proof →
  handoff), mirroring the lean SDD workflow.
- **Confidence:** high. **Status:** accepted.

#### OP-513 — Adopting the lean SDD workflow as a spec

- **Resolution (2026-08-16): accepted —** everything decided in this packet
  is folded into specs in the same implementation pass: a backend-policy spec
  (OP-501…505 rationale + regeneration recipes) and a model-projects spec
  (OP-506…512 contract + the handoff's lean per-model workflow), with
  `AGENTS.md`, `WORKFLOW.md`, and `README.md` updated to match — including
  rewriting the "multitudes" sections to the narrowed durable form (exchange
  format contracts stay; parallel maintained implementations do not).
- **Confidence:** high. **Status:** accepted.

### Residual open points (resolved in the second decision pass)

#### OP-514 — Knob exposure for project generators

- **Question:** `webapp/config/exposure.json` is repo-side and lists, per
  generator, which parameter names are editable through `POST /api/generate`.
  A project generator needs its knobs exposed without editing the repo
  (OP-512 forbids requiring that).
- **Candidates considered:** `exposure` block in `project.yaml` merged with
  the repo file at request time; auto-exposing all project parameters
  (breaks the "few deliberate knobs" principle); a separate `exposure.json`
  in the project folder (a second file for what `project.yaml` already
  scopes).
- **Resolution (2026-08-16): accepted —** the `exposure` block in
  `project.yaml` (per project generator: `editable` names + `preview`
  format), merged at request time under the same validation rules — names
  only, never ranges/units/defaults.
- **Confidence:** high. **Status:** accepted.

#### OP-515 — Exact removal scope: dependencies, probes, and the OpenSCAD path

- **Question:** OP-502/503 drop variant *model* code; what exactly goes with
  it — the `cadquery` extra, the numba floor pin, the `override-dependencies`
  OCP hack, CadQuery probing in `backends.py` / `cadctx info`, the `openscad`
  extra (solidpython2), the OpenSCAD binary fetch in `config/artifacts.yaml`,
  the `scad` export path in `cad_context.exchange`?
- **Candidates considered:** remove CadQuery entirely and keep the OpenSCAD
  toolchain; remove both toolchains; keep both toolchains and remove only
  model code.
- **Resolution (2026-08-16): accepted as modified — OpenSCAD stays live,
  behind its flag, as an optional export format; everything else is removed
  entirely.** Concretely: the `openscad` extra, the binary fetch, and the
  `scad`/STL render path remain available and documented; CadQuery goes
  completely — model code, extra, numba pin, OCP override hack, and backend
  probe. Rationale and easy-recovery information (regeneration recipe) live
  in README and/or the backend-policy spec.
- **Nuance recorded for the spec:** `.scad` is source, not an exchange
  format derivable from an OCCT solid — the flag applies to generators
  *authored* with the OpenSCAD/solidpython2 toolchain (typically project
  generators), whose declared `scad`/STL formats render through the fetched
  binary with the existing degradation rules. It is not an added export of
  build123d models.
- **Confidence:** high. **Status:** accepted.

#### OP-516 — Fate of `cadctx compare`

- **Question:** `compare` sweeps a family across backends and compares
  kernel volumes — meaningless once every family has one implementation.
  It is a documented CLI capability, so its change must be deliberate.
- **Candidates considered:** repurpose as a single-generator proof command;
  drop the command; keep as-is for spec-regenerated variants only.
- **Resolution (2026-08-16): accepted — repurpose and rename.** The family
  sweep disappears with the variants; the replacement command reports one
  generator's kernel volume vs analytic reference vs re-imported mesh
  volume/bounds/watertightness — the routine proof obligation of OP-505 —
  and works on built-ins and project generators alike. Since it no longer
  compares backends, the `compare` name goes with it: proposed name
  **`cadctx verify`** (a naming detail settled at implementation review, not
  a blocking decision). README command reference updated in the same pass.
- **Confidence:** high. **Status:** accepted.

## Implementation Phases

All open points are resolved; phases run in order. Phase 1 precedes phase 2
so regeneration recipes are captured before any deletion.

1. **Spec landing.** Write `specifications/backend-policy/spec.md` (default
   backend, rationale for what was kept, regeneration recipes for the dropped
   variants and for CadQuery recovery, OpenSCAD opt-in export terms with the
   `.scad`-authorship nuance) and
   `specifications/model-projects/spec.md` (project contract OP-506…512 +
   lean per-model SDD workflow). Update `AGENTS.md`, `WORKFLOW.md`,
   `README.md`, and the workspace-layout / agent-interface / web-app specs —
   including the narrowed multitudes rewrite. Recipes are captured **before**
   any deletion.
2. **Variant removal.** Delete `bracket_cadquery.py`, `bracket_openscad.py`,
   `wing_cadquery.py`, their registry entries, exposure entries, and tests;
   remove CadQuery completely (extra, numba pin, OCP override hack, backend
   probe) while keeping the OpenSCAD toolchain live per OP-515; materialize
   the `default` extra; replace `compare` with the renamed single-generator
   proof command (`cadctx verify`, OP-516) and update the README command
   reference; full `pytest` + `ruff` green on the slimmed tree.
3. **Project workspace core.** Resolution chain (OP-506),
   `cadctx project use/clear/init/info`, layout contract (OP-507), split
   output routing through `workspace.py` (OP-509), all reported by
   `cadctx paths`.
4. **Project generators.** In-place dynamic loading per OP-508, merged
   registry with hard-stop collision messages (OP-511), fixture project under
   `tests/` exercised with `CAD_CONTEXT_CACHE` redirected.
5. **Web serving.** Per-generator artifact roots, project grouping in the UI,
   memo invalidation or loud restart requirement (OP-510), `project.yaml`
   exposure merge (OP-514).
6. **Dry validation.** Point the workbench at the real cache-barriere folder:
   `cadctx project use` → `init` → `generators`/`paths`/web listing all
   correct. No model implementation — that is a future project-side packet.

## Dependencies And Risks

- **Deletion is irreversible in the working tree but not in history** — the
  variants remain recoverable from git history and described in previous plan
  packets; the spec recipe is the supported regeneration path. Phase order
  (spec before deletion) is the guard against losing the recipe.
- **OneDrive as a project home:** paths with spaces (already true of the
  example), possible accents, sync-induced file locks during import/export,
  sync latency on fresh artifacts. Mitigations: quoting discipline, atomic
  write-then-rename, and the OP-508 staging fallback. Unmeasured until
  phase 6.
- **Stale server metadata** is a known trap (handoff): any project switch
  must either invalidate the webapp memos or demand a restart loudly.
- **Latency debt (OP-204 carry-forward):** per-request `uv` + OCCT import
  already costs seconds; project-mode path indirection must add no measurable
  overhead. Removing CadQuery/numba from the default install should *improve*
  cold-start resolution and install times; measure before/after in phase 2.
- **Docs drift risk:** the multitudes rule appears in `AGENTS.md`,
  `WORKFLOW.md`, and several specs; phase 1 must sweep all occurrences in one
  pass so no document still promises per-model multi-backend delivery.

## Exit Criteria

Planning (this packet — met 2026-08-16):

- All sixteen OPs carry maintainer resolutions in the summary table;
  `plans/open.md` reflects the state; `test.md` records the review proof.

Implementation:

- Fresh `uv sync --extra default` resolves without CadQuery/numba/OCP
  override baggage; `pytest` + `ruff` green on the slimmed tree.
- No variant backend model code and no CadQuery trace remain in the tree;
  the OpenSCAD toolchain still provisions and degrades correctly; the
  backend-policy spec (and/or README) contains the rationale and a
  regeneration recipe judged sufficient to rebuild a variant without
  consulting git history.
- The renamed proof command (`cadctx verify` or the name settled at review)
  is documented in README and passes on the built-in generators.
- A fixture project proves: resolution chain, in-place generator loading,
  collision hard-stop with a clear message, artifact routing to
  `<project>/cad/`, and web listing/serving from a project — under redirected
  cache.
- The real cache-barriere folder passes the phase-6 dry validation.
- Specs, `AGENTS.md`, `WORKFLOW.md`, `README.md` updated in the same pass; no
  capability exists that is not reachable through a documented `cadctx`
  command.
