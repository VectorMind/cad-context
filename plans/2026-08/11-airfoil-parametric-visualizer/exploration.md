# Exploration: Airfoil Domain — Ideas Excluded From The Plan

Date: 2026-08-11
Status: Reference. Captures the options the maintainer excluded from
`plan.md` at the OP-301/OP-302/OP-303 resolutions (2026-08-11) but judged
worth keeping described: what each brings, its added value, and how it
could be adopted later. Nothing here is committed work.

## aerosandbox (excluded at OP-302)

What it is: a large, actively maintained Python package for aircraft
design and optimization built around airfoil and wing analysis.

What it brings in this repo's context:

- **`Airfoil` class**: a ready-made object model — coordinates, camber
  and thickness queries, repaneling, geometric transforms — replacing
  most of our custom numpy layer.
- **Bundled UIUC database**: thousands of named real-world airfoils
  loadable by name (`Airfoil("dae11")`), no `.dat` parsing of our own.
- **CST (Kulfan) tooling**: fitting and evaluation of the standard
  low-dimensional optimization parameterization — the hard math of a
  future CST family (OP-301) already implemented.
- **XFoil wrapper + NeuralFoil integration**: both aerodynamic-feedback
  paths of OP-303 behind one API.
- **Optimization framework**: gradient-based design optimization (casadi
  underneath) if the repo ever moves from visualization to design.

Added value: one dependency buys the whole airfoil domain — geometry,
database, parameterizations, analysis — with battle-tested numerics.

Cost / why excluded: a big opinionated package with a heavy dependency
tree, overlapping (and thereby competing with) our thin custom layer; the
packet only needs NACA 4-digit math, which is ~50 lines of numpy.

Adoption path if revisited: an optional `[airfoil]` extra in
`pyproject.toml`; our parameter-schema contract stays the interface, with
aerosandbox as one more generator backend behind it (fits the repo's
multitudes rule and the OP-305 switchable-backends rule).

## Aerodynamic feedback in the UI (excluded at OP-303)

The idea: show live aerodynamic numbers (CL/CD/CM, maybe small polar
plots) next to the geometry while the user drags profile sliders — the
step that turns the page from a shape viewer into a design tool.

- **NeuralFoil** (`neuralfoil`): ML surrogate trained on XFoil data;
  millisecond evaluation, pure-Python wheels, no external binary. The
  only option fast enough to track a live slider. Natural UI shape: a
  toggle enabling a CL/CD/CM readout (and optionally a mini polar) fed by
  the same regeneration response.
- **XFoil**: the classic panel-method reference. External binary, slower,
  brittle to automate on Windows — wrong for the live loop, right as a
  validation tool for surrogate numbers. If adopted, its binary should be
  provisioned through Plan 1's config-driven artifact fetch
  (`config/artifacts.yaml` + `cadctx fetch xfoil`), which was designed
  with exactly this reuse in mind.
- What it could look like: geometry stays the committed product; aero
  numbers arrive as an extra `aero` block in the regeneration response,
  rendered as a readout panel — no change to the regeneration contract's
  shape, only an additive field.

## Deferred parameterization families (from OP-301)

- **UIUC `.dat` import**: import/normalize/resample real published
  airfoil coordinates instead of generating them; pairs naturally with
  the aerosandbox bundled database, or with a small custom parser if the
  thin-dependency stance holds.
- **CST (Kulfan)**: smooth low-dimensional shape control, the standard
  for optimization workflows; needs fitting machinery to reproduce named
  airfoils — the main reason it points toward aerosandbox rather than
  custom code.
- **Bezier/B-spline freehand control**: **rejected** at OP-301 (not
  merely deferred) — least aerodynamically grounded, and the UI is not
  meant to want freehand shape editing.
