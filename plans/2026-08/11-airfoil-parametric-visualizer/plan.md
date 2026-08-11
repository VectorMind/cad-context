# Plan: Airfoil Parametric Visualizer Integrated In The Web App

Date: 2026-08-11
Status: Approved — all open points accepted by the maintainer 2026-08-11
(OP-301, OP-302, OP-303, OP-305 with amendments recorded below; excluded
ideas captured in `exploration.md`). Sequenced after Plans 1 and 2: depends
on Plan 1's generator env and Plan 2's viewer + parameter panel +
regeneration bridge. This packet is also the first *real*
stress test of both: a parameter-heavy generator with a live tweak loop.

## Problem Summary

The first driving use case for the whole repository is a parametric airfoil
workflow: pick or generate a profile, adjust its parameters with immediate
2D feedback, and loft it into a 3D wing section — all inside the Plan 2 web
app. Nothing airfoil-specific exists yet, and the key design choices
(parameterization families, whether to include aerodynamic feedback, loft
backend) are open.

## Resolution Summary

All open points accepted by the maintainer 2026-08-11 (OP-301, OP-302,
OP-303, OP-305 with amendments; ideas excluded from scope are described in
`exploration.md`, same folder). One-glance state (details in the Open
Points section below):

| OP | Topic | Accepted Resolution | Confidence | Status |
| --- | --- | --- | --- | --- |
| OP-301 | Profile parameterization families | **NACA 4-digit only** this packet; Bezier freehand **rejected**; UIUC `.dat` import and CST deferred, recorded in `exploration.md` | high | accepted |
| OP-302 | Airfoil library dependency | **custom numpy only**; aerosandbox excluded from this plan entirely — its capabilities and adoption paths documented in `exploration.md` | high | accepted |
| OP-303 | Aerodynamic feedback in the UI | **geometry only**; NeuralFoil stretch dropped from this packet too; NeuralFoil/XFoil ideas recorded in `exploration.md` | high | accepted |
| OP-304 | 2D profile rendering in the web app | client-side plot component (plain inline SVG in React) from coordinates JSON produced by the Python generator; server-side SVG stays as the downloadable file artifact | high | accepted |
| OP-305 | Loft backend for the 3D wing section | **both** build123d and CadQuery lofts, user-switchable in the app to compare; trimesh-skinning preview **rejected** (real generator outputs only); latency accepted — spinner + debounce | high | accepted |

## Goal And Objectives

- An airfoil generator module in the Python package producing 2D profile
  coordinates and exports (SVG/DXF) from parameters.
- A 3D wing-section loft (chord, span, taper, twist, sweep) through both
  Plan 1 B-rep backends (build123d and CadQuery), user-switchable in the
  app, exported to GLB for the viewer.
- A dedicated web-app page: 2D profile view with live parameter sliders,
  3D lofted view, both driven by the Plan 2 regeneration bridge.
- Parameter schema published through the generic parameter-schema contract
  so the page's controls are generated, not hand-wired.

## Scope And Non-Goals

In scope: NACA 4-digit profile generation, loft, 2D+3D visualization,
parametric interactivity.

Non-goals (this packet): CFD, full polar analysis pipelines, wing
structural design, multi-section blended wings, export to flight-sim or
CAM formats. Profile import (UIUC `.dat`) and CST parameterization are
deferred (OP-301). Aerodynamic *preview* numbers are excluded (OP-303).
Both sets of excluded ideas are described in `exploration.md`.

## Open Points

### OP-301 — Profile parameterization families

- Options (not mutually exclusive — the repo rule is multitudes):
  - **NACA 4/5-digit analytic**: ~50 lines of numpy, zero deps, exact
    textbook math, instant evaluation. The obvious baseline.
  - **UIUC coordinate database import** (`.dat` files): thousands of real
    airfoils; import/normalize/resample rather than generate.
  - **CST (Kulfan) parameterization**: smooth low-dimensional shape control,
    the standard for optimization workflows; more math, needs fitting to
    reproduce named airfoils.
  - **Bezier/B-spline control points**: most direct for hand-tweaking in a
    UI; least aerodynamically grounded.
- Proposal: ship **NACA 4-digit first** (proves the whole loop with zero
  deps), then **UIUC .dat import** second; CST third as the optimization-
  ready family; Bezier only if the UI proves to want freehand control.
- Confidence: high. Status: **accepted 2026-08-11 with amendment** —
  **NACA 4-digit only** in this packet. Bezier freehand control is
  **rejected**. UIUC `.dat` import and CST are excluded from this plan;
  they are recorded in `exploration.md` as future candidates.

### OP-302 — Airfoil library dependency

- Options:
  - **Custom numpy implementation** (no new dep): full control, trivially
    testable against published NACA coordinates.
  - **aerosandbox**: `Airfoil` class, UIUC database bundled, CST tools,
    XFoil wrapper, NeuralFoil integration — one dep buys the whole domain,
    but it is a large opinionated package.
  - **airfoils** (PyPI): small NACA-4 class; abandoned-ish, adds little
    over custom.
- Proposal: **custom numpy for NACA + .dat parsing** (the math is small and
  the repo keeps control), with **aerosandbox as an optional `[airfoil]`
  extra** adopted only when CST/analysis (OP-303) needs it — not before.
- Confidence: high. Status: **accepted 2026-08-11 with amendment** —
  **custom numpy only**; aerosandbox is excluded from this plan entirely,
  not even reserved as an optional extra. What it can do, the added value
  it would bring, and possible adoption paths are described in
  `exploration.md`.

### OP-303 — Aerodynamic feedback in the UI

- Options:
  - **None (geometry only)** for this packet.
  - **NeuralFoil** (`neuralfoil`): ML surrogate giving CL/CD/CM in
    milliseconds, pure-Python wheels, no XFoil binary — fast enough to
    update live alongside sliders.
  - **XFoil binary wrapper**: the classic reference, but an external
    binary, slower, and brittle to automate on Windows.
- Proposal: **geometry-only for the committed scope**, with a stretch phase
  wiring **NeuralFoil** behind a toggle (it fits the live-slider loop where
  XFoil cannot). XFoil rejected for this packet, noted as a future
  validation tool.
- Confidence: high. Status: **accepted 2026-08-11 with amendment** —
  **geometry only**, and the NeuralFoil stretch phase is dropped from this
  packet as well. The NeuralFoil and XFoil options, and what a live aero
  readout could add, are recorded in `exploration.md`.

### OP-304 — 2D profile rendering in the web app

- Options: reuse the Plan 2 generic SVG viewer (server-rendered SVG per
  change) vs a **client-side plot component** (SVG/canvas drawn in React
  from a coordinates JSON payload) with axes, camber line, thickness
  overlays.
- Proposal: **client-side plot from coordinates JSON** — profile tweaking
  wants sub-frame redraws and overlays (camber line, max-thickness marker)
  that a generic file viewer can't give; coordinates are tiny payloads.
  The server-side SVG export stays as the *file* artifact for download.
- Confidence: high. Status: **accepted 2026-08-11** as proposed, with the
  rendering technique fixed below.

**Resolution detail (2026-08-11): rendering technique — plain inline SVG
in React.** No canvas, no charting library:

- The regeneration response carries a small `coords` JSON artifact
  (upper/lower surface points, camber line, max-thickness marker — on the
  order of 200 points) produced by the Python generator. The plot never
  recomputes geometry client-side, per the OP-305 real-generators-only
  rule.
- The component maps coordinates through two linear scale helpers into
  one SVG `path` per curve (outline, dashed camber line), plus axis
  ticks and a light grid; pan/zoom via `viewBox` updates.
- SVG over canvas because the point count is tiny (render cost is
  negligible), lines stay crisp at any zoom, and overlays/hover/theming
  come free via DOM + CSS. Canvas only pays off at tens of thousands of
  points or animation loops; a charting library adds nothing at this
  size.

### OP-305 — Loft backend for the 3D wing section

- Options: CadQuery loft vs build123d loft (both OCCT `loft` through
  section wires) vs trimesh skinning (mesh-level, fastest, no B-rep).
- Proposal: implement in **build123d first** (its algebra API makes
  sectioned lofts terse), keep a CadQuery twin as the cross-backend
  comparison per repo rule, and use **trimesh skinning for the live
  preview path** if OCCT loft latency hurts the slider loop (mirrors the
  Plan 2 OP-204 fast/slow split: fast mesh preview, exact B-rep export).
- Confidence: high. Status: **accepted 2026-08-11 with amendment** below.

**Amendment (accepted 2026-08-11): multiple real implementations,
user-switchable; no approximations; latency is acceptable.** For big
library decisions defined at the spec/concept level, the rule is:

- Implement **multiple real implementations** where the spec admits them
  (here: **build123d and CadQuery** lofts), and let the user **switch the
  selection in the app** to compare outputs directly.
- **No approximation paths** that deviate from what a real generator
  produces: the trimesh-skinning preview is **rejected** (same reasoning
  as Plan 2's OP-204 WASM rejection — the app renders real backend
  outputs only).
- **Latency is not a problem** in this type of app: a spinner or similar
  busy indicator during regeneration is fully acceptable; the debounced,
  latest-wins regeneration contract already bounds the load.

This is a durable, wisdom-level rule — fold it into `specifications/`
alongside the regeneration and parameter-schema contracts at the next
spec fold.

## Implementation Phases

0. **Decisions.** Done 2026-08-11 — OP-301…OP-305 accepted (amendments
   recorded above); excluded ideas captured in `exploration.md`.
1. **Profile core.** NACA 4-digit generator in `cad_context.airfoil`;
   pytest against published coordinate tables; SVG/DXF export via Plan 1's
   2D stack.
2. **Loft.** Wing-section loft (chord/span/taper/twist/sweep) in **both**
   build123d and CadQuery (OP-305); STEP + GLB export per backend;
   volume/bounds proof and cross-backend agreement.
3. **Web page.** Airfoil page in the Plan 2 app: generated parameter
   panel, client-side inline-SVG profile plot (OP-304), 3D GLB view with
   a backend selector (OP-305), regeneration loop wired end-to-end with a
   spinner while regenerating.
4. **Proof.** Coordinate-table matches, loft measurements per backend,
   page interaction loop and latency in `test.md`.

## Dependencies And Risks

- Hard dependency on Plan 1 (backends, exports, parameter models) and
  Plan 2 (viewer, panel, regeneration bridge); this packet should not
  start implementation before those packets' matching phases are proven.
- Regeneration latency is explicitly accepted (OP-305 amendment): the 2D
  plot redraws from tiny coordinate payloads, the 3D loft shows a spinner
  behind the debounced, latest-wins contract — no live-drag promise and
  no approximation path.
- Trailing-edge closure and self-intersection on extreme parameters need
  guard rails (parameter ranges in the schema, geometry validity checks).

## Exit Criteria

- NACA 4-digit coordinates match published references within tolerance.
- A lofted wing section exports valid STEP and GLB from **both** backends
  (loads back, sane volume/bounds, cross-backend volume agreement).
- In the web app: dragging profile sliders updates the 2D plot through
  the regeneration contract (latest-wins debounce); the 3D loft updates
  on parameter change with a spinner while regenerating; switching the
  loft backend re-renders the other implementation's output; all recorded
  with timings in `test.md`.
