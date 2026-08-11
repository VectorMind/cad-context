# Plan: Airfoil Parametric Visualizer Integrated In The Web App

Date: 2026-08-11
Status: Planning — open points below need maintainer decisions. Sequenced
after Plans 1 and 2: depends on Plan 1's generator env and Plan 2's viewer +
parameter panel + regeneration bridge. This packet is also the first *real*
stress test of both: a parameter-heavy generator with a live tweak loop.

## Problem Summary

The first driving use case for the whole repository is a parametric airfoil
workflow: pick or generate a profile, adjust its parameters with immediate
2D feedback, and loft it into a 3D wing section — all inside the Plan 2 web
app. Nothing airfoil-specific exists yet, and the key design choices
(parameterization families, whether to include aerodynamic feedback, loft
backend) are open.

## Goal And Objectives

- An airfoil generator module in the Python package producing 2D profile
  coordinates and exports (SVG/DXF) from parameters.
- A 3D wing-section loft (chord, span, taper, twist, sweep) through the
  Plan 1 B-rep backends, exported to GLB for the viewer.
- A dedicated web-app page: 2D profile view with live parameter sliders,
  3D lofted view, both driven by the Plan 2 regeneration bridge.
- Parameter schema published through the generic parameter-schema contract
  so the page's controls are generated, not hand-wired.

## Scope And Non-Goals

In scope: profile generation, profile import, loft, 2D+3D visualization,
parametric interactivity.

Non-goals (this packet): CFD, full polar analysis pipelines, wing
structural design, multi-section blended wings, export to flight-sim or
CAM formats. Aerodynamic *preview* numbers are an open point (OP-303), not
a committed goal.

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
- Confidence: high on NACA-first sequencing; medium on CST priority.
  Status: proposed.

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
- Confidence: medium — aerosandbox-from-day-one is a defensible opposite
  call; the plan prefers thin first. Status: proposed.

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
- Confidence: high on geometry-first; medium on NeuralFoil landing inside
  this packet vs. a follow-up. Status: proposed.

### OP-304 — 2D profile rendering in the web app

- Options: reuse the Plan 2 generic SVG viewer (server-rendered SVG per
  change) vs a **client-side plot component** (SVG/canvas drawn in React
  from a coordinates JSON payload) with axes, camber line, thickness
  overlays.
- Proposal: **client-side plot from coordinates JSON** — profile tweaking
  wants sub-frame redraws and overlays (camber line, max-thickness marker)
  that a generic file viewer can't give; coordinates are tiny payloads.
  The server-side SVG export stays as the *file* artifact for download.
- Confidence: high. Status: proposed.

### OP-305 — Loft backend for the 3D wing section

- Options: CadQuery loft vs build123d loft (both OCCT `loft` through
  section wires) vs trimesh skinning (mesh-level, fastest, no B-rep).
- Proposal: implement in **build123d first** (its algebra API makes
  sectioned lofts terse), keep a CadQuery twin as the cross-backend
  comparison per repo rule, and use **trimesh skinning for the live
  preview path** if OCCT loft latency hurts the slider loop (mirrors the
  Plan 2 OP-204 fast/slow split: fast mesh preview, exact B-rep export).
- Confidence: medium. Status: proposed.

## Implementation Phases

0. **Decisions.** Maintainer resolves OP-301…OP-305.
1. **Profile core.** NACA 4-digit generator + `.dat` import/resample in
   `cad_context.airfoil`; pytest against published coordinate tables;
   SVG/DXF export via Plan 1's 2D stack.
2. **Loft.** Wing-section loft (chord/span/taper/twist/sweep) per OP-305;
   STEP + GLB export; volume/bounds proof.
3. **Web page.** Airfoil page in the Plan 2 app: generated parameter
   panel, client-side 2D profile plot (OP-304), 3D GLB view, regeneration
   loop wired end-to-end.
4. **Stretch.** NeuralFoil toggle per OP-303 resolution.
5. **Proof.** Coordinate-table matches, loft measurements, page
   interaction loop and latency in `test.md`.

## Dependencies And Risks

- Hard dependency on Plan 1 (backends, exports, parameter models) and
  Plan 2 (viewer, panel, regeneration bridge); this packet should not
  start implementation before those packets' matching phases are proven.
- Slider-rate regeneration is the riskiest UX promise — mitigations
  already built into OP-304 (client-side 2D) and OP-305 (mesh preview
  path); the 3D loft may accept a debounced update instead of live drag.
- Trailing-edge closure and self-intersection on extreme parameters need
  guard rails (parameter ranges in the schema, geometry validity checks).

## Exit Criteria

- NACA 4-digit coordinates match published references within tolerance;
  a UIUC `.dat` file imports and renders.
- A lofted wing section exports valid STEP and GLB (loads back, sane
  volume/bounds).
- In the web app: dragging profile sliders updates the 2D plot at
  interactive rates; the 3D loft updates on parameter change (debounced
  acceptable); both recorded with timings in `test.md`.
