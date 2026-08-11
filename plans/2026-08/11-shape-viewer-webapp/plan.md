# Plan: Visualization Web App For Generated Shapes

Date: 2026-08-11
Status: Planning — open points below need maintainer decisions. No
`package.json` exists yet by design; it is materialized from OP resolutions.
Depends on Plan 1 (`plans/2026-08/11-cad-generators-bringup/`) for the
exchange-format contract (GLB/STL/SVG) it renders.

## Problem Summary

Generated geometry currently has no quick human-facing surface. Desktop
viewers exist and are often better for deep inspection, but the recurring
need is a **fast preview-and-tweak loop**: change a parameter, regenerate,
see the shape — especially for parametric workflows with lots of adjustment
(the Plan 3 airfoil generator is the first driving use case). The web app is
deliberately a *quick preview and parametric helper*, not a CAD viewer
replacement.

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
  regeneration API surface (OP-204). Vite SPA is the fallback if Astro SSR
  proves to be overhead for a mostly-client app.
- Confidence: medium-high — precedent is strong, but unlike evidence-engine
  this app is client-heavy, which is Vite's home turf. Status: proposed.

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
- Confidence: high. Status: proposed.

### OP-203 — Parameter controls UI

- Options: **leva** (r3f-ecosystem control panel, schema-driven, fastest to
  wire) vs **tweakpane** (framework-agnostic, polished) vs custom React
  forms (most work, most control, needed eventually for rich inputs like
  airfoil pickers).
- Proposal: **leva** for the generic panel now — its schema-driven API maps
  almost 1:1 onto the parameter-schema contract; accept that Plan 3 may add
  custom components alongside it.
- Confidence: medium. Status: proposed.

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
  documented mode for demos, and (d) explicitly deferred.
- Confidence: high on the a→b sequencing; low on how far (a) alone can
  carry interactive sliders. Status: proposed.

### OP-205 — Package manager and tooling

- Proposal: **pnpm**, TypeScript, and the framework's own dev server;
  no test framework in the first pass beyond `tsc`/build passing (viewer
  proof is visual + loader round-trip). Prettier defaults.
- Confidence: medium (pnpm matches astro-huge-doc precedent). Status:
  proposed.

## Proposed `package.json` Sketch

Materialized only after OP-201…OP-205 are accepted (shown for the Astro
proposal; a Vite resolution changes the first three deps only):

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

0. **Decisions.** Maintainer resolves OP-201…OP-205.
1. **Scaffold.** `webapp/` created per accepted framework; `package.json`,
   TypeScript, layout shell (reusing astro-huge-doc theme if OP-201 lands
   on Astro).
2. **Static viewers.** GLB/STL 3D viewer page and SVG 2D viewer page,
   loading artifacts from `out/` produced by Plan 1's demos.
3. **Parameter panel.** Generic panel rendered from a parameter-schema JSON
   (contract co-designed with Plan 1's pydantic models; folded into
   `specifications/parameter-schema/spec.md` when accepted).
4. **Regeneration loop.** OP-204 mode (a): endpoint → `cadctx` → fresh
   artifact → viewer refresh; measure the latency to ground the (b)
   decision with numbers.
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
- Measured regeneration latency recorded in `test.md`, with a go/no-go
  note on escalating OP-204 to mode (b).
