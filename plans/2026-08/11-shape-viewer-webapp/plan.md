# Plan: Visualization Web App For Generated Shapes

Date: 2026-08-11
Status: Approved — all open points accepted by the maintainer 2026-08-11
(OP-201 and OP-204 with amendments recorded below). No `package.json`
exists yet by design; it is materialized from the accepted decisions when
Phase 1 starts. Depends on Plan 1
(`plans/2026-08/11-cad-generators-bringup/`) for the exchange-format
contract (GLB/STL/SVG) it renders.

## Problem Summary

Generated geometry currently has no quick human-facing surface. Desktop
viewers exist and are often better for deep inspection, but the recurring
need is a **fast preview-and-tweak loop**: change a parameter, regenerate,
see the shape — especially for parametric workflows with lots of adjustment
(the Plan 3 airfoil generator is the first driving use case). The web app is
deliberately a *quick preview and parametric helper*, not a CAD viewer
replacement.

## Resolution Summary

All open points accepted by the maintainer 2026-08-11. OP-201 dropped the
Vite-SPA fallback (Astro SSR + islands per page is the decision, reusing
the maintainer-owned astro-huge-doc codebase wholesale); OP-204 gained an
explicit frontend↔backend regeneration contract with single-parameter
updates and latest-wins debouncing, and rejected the WASM option outright.
OP-203's parameter-exposure idea was folded back into Plan 1 as a simple
parametric demo shape. One-glance state (details in the Open Points
section below):

| OP | Topic | Accepted Resolution | Confidence | Status |
| --- | --- | --- | --- | --- |
| OP-201 | Web framework | Astro SSR + React islands per page; astro-huge-doc (maintainer-owned) reused as the codebase — full copy reuse; no SPA fallback | high | accepted |
| OP-202 | 3D rendering stack | react-three-fiber + drei (GLTFLoader, STLLoader, OrbitControls, Grid, Edges); `<model-viewer>` noted for zero-effort embeds | high | accepted |
| OP-203 | Parameter controls UI | leva for the generic schema-driven panel; rework later only if needed; Plan 1 amended to add a simple parametric demo shape | medium | accepted |
| OP-204 | Regeneration bridge | subprocess-per-request (a) behind a designed regeneration contract: full params + optional single-changed-parameter field, one request in flight, latest-wins debounce; warm worker (b) drops in unchanged; sweeps (c) demo mode; WASM (d) **rejected** | high | accepted |
| OP-205 | Package manager and tooling | pnpm + TypeScript + Prettier defaults; no test framework in first pass beyond build passing | medium | accepted |

## Positioning Against External Viewers

Per WORKFLOW.md scope ownership, integrate rather than rebuild. The web app
coexists with, and plans should keep documenting, the better-for-the-job
alternatives:

- **ocp_vscode / OCP CAD Viewer** (VS Code extension): best-in-class for
  CadQuery/build123d dev loops — shows tessellated B-rep with real edges,
  live from Python. The web app does not compete with this for in-editor
  work.
- **CQ-editor**: desktop CadQuery IDE.
- **FreeCAD**: full desktop CAD for STEP inspection and measurement.
- Online viewers (e.g. 3dviewer.net) for one-off file checks.

The web app's niche: browser-based, shareable/demoable, parameter panels
wired to regeneration, and 2D+3D side by side.

## Goal And Objectives

- A web app scaffolded under `webapp/` with its own `package.json`.
- Load and render 3D exports (GLB primary, STL fallback) with orbit
  controls, grid, and basic material/edges toggle.
- Render 2D exports (SVG) inline with pan/zoom.
- A generic parameter panel driven by the parameter-schema contract
  (generator declares parameters; app renders controls; change triggers
  regeneration and re-render).
- A regeneration bridge to the Python side (OP-204).

## Scope And Non-Goals

In scope: framework/scaffold, 3D+2D viewers, parameter panel, regeneration
bridge, demo page listing artifacts from `out/`.

Non-goals: measurement/sectioning tools, STEP parsing in the browser,
assemblies, auth/multi-user, hosting/deployment, mobile polish. Airfoil
specifics stay in Plan 3.

## Open Points

### OP-201 — Web framework

- Options:
  - **Astro (SSR) + React islands**: maintainer precedent — both
    `astro-huge-doc` and evidence-engine's web viewer use exactly this
    stack; layout shell/theme reusable from `astro-huge-doc`.
  - **Vite + React SPA**: lightest scaffold, no SSR machinery; everything is
    client-side anyway for a 3D viewer.
  - **Next.js**: mainstream, but brings the most framework weight for no
    identified need here.
- Proposal: **Astro + React islands** for consistency with the maintainer's
  existing stacks and reusable layout/theme; SSR endpoints double as the
  regeneration API surface (OP-204).
- Confidence: high (raised from medium-high at acceptance). Status:
  **accepted 2026-08-11 with amendment** — the Vite-SPA fallback is
  dropped. The maintainer owns astro-huge-doc in full, making it a strong
  asset for **full copy reuse** as the starting codebase, not just a theme
  source. Keep SSR simple — no SPA machinery; React islands per page are
  fully sufficient for this app.

### OP-202 — 3D rendering stack

- Options:
  - **three.js via react-three-fiber (+ drei)**: full control, GLB/STL
    loaders, orbit controls, huge ecosystem; pairs naturally with React
    islands.
  - **`<model-viewer>` web component**: near-zero code for GLB display, but
    GLB-only and hard to extend (no custom overlays, no STL, limited
    camera/scene control).
  - **three-cad-viewer** (the viewer under ocp_vscode): CAD-native look
    (edges, clipping) but designed around its own tessellation format, not
    generic GLB.
  - **vtk.js / xeokit**: powerful but heavy and aimed at scientific/BIM
    niches.
- Proposal: **react-three-fiber + drei** as the base (GLTFLoader +
  STLLoader, OrbitControls, Grid, Edges). Keep `<model-viewer>` noted as a
  zero-effort embed for docs/demos. Revisit three-cad-viewer if B-rep edge
  fidelity becomes a requirement.
- Confidence: high. Status: **accepted 2026-08-11** as proposed.

### OP-203 — Parameter controls UI

- Options: **leva** (r3f-ecosystem control panel, schema-driven, fastest to
  wire) vs **tweakpane** (framework-agnostic, polished) vs custom React
  forms (most work, most control, needed eventually for rich inputs like
  airfoil pickers).
- Proposal: **leva** for the generic panel now — its schema-driven API maps
  almost 1:1 onto the parameter-schema contract; accept that Plan 3 may add
  custom components alongside it.
- Confidence: medium — the maintainer is not yet familiar with these
  libraries; leva is accepted as a try-first choice, to be reworked later
  **only if needed**. Status: **accepted 2026-08-11**.

**Cross-plan note (accepted 2026-08-11): parameter exposure lands on the
CAD side too.** The idea of shapes exposing a small set of parameters is
relevant to the Python generators generally, not only to this app. Plan 1
(`11-cad-generators-bringup`) is amended accordingly: its demo work now
includes a **simple parametric example** — one shape exposing a few
parameters through the pydantic parameter-schema models and a documented
`cadctx` command. The web app also reaches that example through the shared
parameter-schema spec once it is folded.

### OP-204 — Regeneration bridge (browser → Python → new geometry)

- Options:
  - **(a) Subprocess per request**: server endpoint spawns
    `cadctx generate ... --json`, returns fresh GLB/SVG. Simple, stateless,
    but pays interpreter + OCCT import cost per change (seconds — too slow
    for slider-dragging).
  - **(b) Long-lived Python worker**: FastAPI (or stdio JSON-RPC child
    process) keeping kernels warm; sub-100ms regeneration for light
    parts. More moving parts.
  - **(c) Precomputed sweeps**: generate a parameter grid ahead of time;
    the app only switches between cached artifacts. Zero latency, but only
    works for low-dimensional parameter spaces.
  - **(d) In-browser compute**: e.g. manifold's WASM build or openscad-wasm
    for CSG previews without any server round-trip. Attractive long-term,
    but forks the geometry code path (violates single-implementation rule
    for the B-rep backends, which have no WASM).
- Proposal: **start with (a)** to prove the loop end-to-end, with the
  endpoint interface designed so **(b)** slots in behind it unchanged (same
  request/response contract, warm worker as a drop-in). Keep (c) as a
  documented mode for demos.
- Confidence: high on the a→b sequencing; low on how far (a) alone can
  carry interactive sliders — the contract amendment below is the
  mitigation. Status: **accepted 2026-08-11 with amendments** — (d) is
  **rejected outright**, not merely deferred: no WASM, the app benefits
  from real renderers of the real backend outputs only; and the
  frontend↔backend contract is designed explicitly, below.

**Amendment (accepted 2026-08-11): explicit regeneration contract with
debounced, latest-wins requests.** The frontend↔backend interface is a
designed contract, not an ad-hoc endpoint, so that slider interaction
never overloads the generation pipeline:

- **Request** — `POST /api/generate` with
  `{ generator, params, changed?, seq }`:
  - `generator`: the generator id (matches the parameter-schema contract).
  - `params`: always the **full** parameter set — keeps mode (a)
    stateless.
  - `changed`: optional name of the **single parameter** that moved (the
    slider case). Mode (a) ignores it; a warm worker (b) may use it for
    incremental regeneration — supporting single-parameter interaction
    without a contract change.
  - `seq`: client-side monotonically increasing sequence number.
- **Response** — `{ seq, artifacts, timings }` where `artifacts` maps
  format to URL (`glb`, `svg`, …) and `timings` reports at least total
  generation milliseconds (feeds the (b) go/no-go). Errors return
  `{ seq, error }`.
- **Client concurrency rule** — at most **one request in flight**. While a
  request is running, further parameter changes are debounced and collapse
  into a single pending latest-values request; it is dispatched only when
  the in-flight request completes. Responses whose `seq` is older than the
  newest dispatched request are discarded, so a stale render never
  overwrites a fresh one. Sliders therefore cost at most one queued
  request no matter how fast they move.
- The contract is co-owned with the parameter-schema work and is folded
  into `specifications/` (alongside the parameter-schema spec) at the
  spec-fold step.

### OP-205 — Package manager and tooling

- Proposal: **pnpm**, TypeScript, and the framework's own dev server;
  no test framework in the first pass beyond `tsc`/build passing (viewer
  proof is visual + loader round-trip). Prettier defaults.
- Confidence: medium (pnpm matches astro-huge-doc precedent). Status:
  **accepted 2026-08-11** as proposed.

## Proposed `package.json` Sketch

Reflects the accepted decisions; materialized as a real file when Phase 1
starts:

```jsonc
{
  "name": "cad-context-webapp",
  "private": true,
  "scripts": { "dev": "astro dev", "build": "astro build" },
  "dependencies": {
    "astro": "^5",
    "@astrojs/node": "^9",
    "@astrojs/react": "^4",
    "react": "^19",
    "react-dom": "^19",
    "three": "^0.1xx",
    "@react-three/fiber": "^9",
    "@react-three/drei": "^10",
    "leva": "^0.10"
  },
  "devDependencies": { "typescript": "^5", "@types/three": "^0.1xx" }
}
```

(Version ranges are indicative; exact pins land with the lockfile at
implementation time.)

## Implementation Phases

0. **Decisions.** Done 2026-08-11 — OP-201…OP-205 accepted (OP-201, OP-204
   amended); this plan updated to the accepted state.
1. **Scaffold.** `webapp/` created from the astro-huge-doc codebase (full
   copy reuse per OP-201); `package.json`, TypeScript, layout shell.
2. **Static viewers.** GLB/STL 3D viewer page and SVG 2D viewer page,
   loading artifacts from `out/` produced by Plan 1's demos.
3. **Parameter panel.** Generic panel rendered from a parameter-schema JSON
   (contract co-designed with Plan 1's pydantic models; folded into
   `specifications/parameter-schema/spec.md` when accepted).
4. **Regeneration loop.** OP-204 mode (a) behind the accepted regeneration
   contract: endpoint → `cadctx` → fresh artifact → viewer refresh, with
   the `seq`/latest-wins debounce client implemented from the start;
   measure the latency to ground the (b) decision with numbers.
5. **Proof.** Load round-trips and the regeneration loop recorded in
   `test.md` with timings.

## Dependencies And Risks

- Depends on Plan 1 exporting GLB/SVG (its Phases 1–3) and on the
  parameter-schema contract (co-owned with Plan 1's OP-106 pydantic
  models).
- Subprocess latency (OP-204a) may be too slow for real slider
  interactivity — mitigated by the planned (b) upgrade path.
- three.js version churn vs. drei/fiber compatibility; pin via lockfile.

## Exit Criteria

- `pnpm build` clean from a clean checkout.
- A Plan 1 GLB artifact renders with orbit controls; an SVG artifact
  renders with pan/zoom.
- Changing a parameter in the panel produces a regenerated shape on screen
  without restarting the app.
- Dragging a slider keeps at most one generation request in flight, with
  intermediate values coalesced (latest-wins) and stale responses
  discarded — observable in the regeneration-loop test (OP-204 contract).
- Measured regeneration latency recorded in `test.md`, with a go/no-go
  note on escalating OP-204 to mode (b).
