# Workflow

This repository is spec-driven. It uses durable specifications for binding
contracts and dated plans for time-bounded implementation work.

`cad-context` is a workbench for programmatic CAD: generating 2D vector
geometry and 3D shapes from Python code, with a companion web app for quick
interactive preview and parametric adjustment of the generated shapes.

## Guiding Principle: Focused Core, Portable Contracts

The core minimizes maintained implementation debt: build123d is the maintained
3D B-rep path, Shapely the 2D path, and trimesh the mesh/GLB bridge. OpenSCAD is
an optional project toolchain for SCAD-specific delivery. Routine models are not
duplicated across wrappers.

Geometry remains portable because shared behavior is defined by contracts over
exchange formats (STEP, STL, GLB, SVG, DXF, JSON, SCAD), never by one backend's
native object model. Risk-triggered alternative implementations belong in the
external model project and do not become permanent core maintenance by default.

## Spec Maintenance

Keep `specifications/` current as durable decisions emerge. Whenever the
maintainer states a strategy, policy, contract, or wisdom-level rule — or work
settles such a decision — fold it into the relevant spec in the same pass, not
just into a plan or a commit message. Plans are time-bounded and get abandoned
after implementation; the spec is what survives. Do not record case-level
implementation detail in the spec; capture the durable rule behind it.

## Generated Artifacts

Generated geometry is derived data. Built-in output belongs under `.cache/cad/`;
an external model project's durable output belongs under its `cad/` directory.
Neither is committed or mixed into repository `specifications/` or `plans/`.
Checked-in project fixtures contain source only and are copied to temporary
directories before generation.

## Git Ownership

The maintainer owns all git operations. Assistants and tools must not run
`git add`, `git commit`, `git push`, branch, or any other history-changing git
command. Leave finished work in the working tree and let the maintainer
review, stage, and commit it.

## Areas

### `specifications/`

Use `specifications/` for durable requirements that constrain implementation
across more than one pass.

Create a specification under:

```text
specifications/<slug>/spec.md
```

Specifications contain timeless binding rules and contracts:

- generator capabilities, inputs, outputs, and export semantics;
- exchange-format contracts (which formats each backend must emit, units,
  coordinate conventions, tessellation quality knobs);
- parameter-schema contracts between generators and the web app;
- accepted non-goals and unsupported behavior.

Specifications must not read like plans or history. Avoid wording such as
"planned", "future", "previously", or "we decided". Put implementation history
in `implementation.md` instead.

### `plans/`

Use `plans/` for dated planning packets tied to active work.

Each plan folder uses:

```text
plans/YYYY-MM/
  DD-<slug>/
    survey.md            # only when the maintainer explicitly requests one
    plan.md
    implementation.md    # created only after implementation work has happened
    test.md
```

Create `survey.md` only when the maintainer explicitly requests a survey. Do
not produce one as a default step; fold light discovery notes into `plan.md`
instead.

Two index files at the top of `plans/` track packet status: `closed.md` lists
completed packets with their proof, and `open.md` lists packets with work
still outstanding. Update these tables whenever a plan is finished or started
so the current state of all plans is visible at a glance.

## Plan Shape

`plan.md` must stay focused on the work package. It should contain:

- problem summary;
- resolution summary;
- goal and objectives;
- scope and non-goals;
- open points with resolution status;
- implementation phases;
- dependencies and risks;
- exit criteria.

Open points should be tracked across the discussion. Use stable IDs such as
`OP-001`, keep the current status visible, and record the resolution only when
the answer is accepted. In this repository every open point that selects a
dependency, framework, or tool must list the candidate options with a short
argument each, name a proposal, and carry a confidence level (`high` /
`medium` / `low`) alongside its status.

The resolution summary, placed directly after the problem summary, carries a
**one-glance table of every open point and design decision** with columns for
OP id, topic, proposal (the accepted resolution once decided), confidence,
and status. The table is the at-a-glance state of the plan's decisions and is
updated in the same pass whenever an open point changes status; the full
candidate options and arguments stay in the detailed Open Points section
below it.

`plan.md` does not need detailed rewrites for every implementation deviation.
Once implementation starts, facts about what actually landed belong in
`implementation.md`.

## Implementation Log

Create `implementation.md` only once implementation work has actually
happened; it logs facts really implemented, never planned intent. A packet
that is still in planning or review has no `implementation.md`.

Every `implementation.md` opens with a **Progress** section — the first
section after the title — and it is updated on every change to the file. It is
a one-glance progress bar, not prose:

- one line with a bar of filled/empty blocks plus the current phase, e.g.
  `` `▰▰▰▱▱▱ Phase 3/6` ``, using the plan's own phase or milestone names;
- one short clause naming the phase in progress and what comes next;
- when the packet is fully implemented and proven, the bar is full and the
  line reads `Done`, e.g. `` `▰▰▰▰▰▰ Done` `` with a one-clause summary and
  any non-blocking follow-ups.

Keep the Progress section to two lines at most; the running detail belongs in
the log below. Use the rest of the file as the running trace of work:

- files changed;
- implementation facts;
- decisions made during development;
- deviations from the plan;
- follow-up risks;
- important commands or migrations.

The implementation log should describe what happened, not restate the whole
plan.

## Test Proof

Use `test.md` as proof of behavior:

- commands run;
- fixtures used;
- expected results;
- actual results;
- known gaps;
- environment or dependency notes that affect reproducibility.

For planning-only changes, `test.md` may record document review and
consistency checks instead of runtime proof.

For geometry work, proof means verifiable exports: a generator run producing
a file, plus a check that the file is valid (opens in a reference tool,
round-trips through a loader, or matches expected measurable properties such
as bounding box, volume, or vertex count) — never "looks right" alone.

## Scope Ownership

`cad-context` owns the supported generator toolkit, external-project contract,
exchange-format contracts, and companion preview app. Model-specific evidence,
code, and SDD documents belong to the external project. It does not compete
with full desktop CAD (FreeCAD, commercial
tools) or with dedicated viewers — where an external viewer is better for a
job, plans should say so and integrate rather than rebuild.
