# Open Plans

Plan packets with work still outstanding. See each folder for details.

- [CAD Generators Python Environment Bringup](./2026-08/11-cad-generators-bringup/plan.md)
  — approved 2026-08-11: OP-101…OP-107 all accepted (OP-103 amended with a
  config-driven GitHub-releases fetch script for external binaries; OP-106
  amended to make the documented `cadctx` CLI the single human/agent
  interface — no skills, routing via README/AGENTS docs; OP-106 further
  amended 2026-08-11 from Plan 2: a simple parametric demo shape exposing
  a few parameters via the parameter-schema models and the CLI).
  Implementation not started; Phase 1 materializes `pyproject.toml`.
  Unblocks Plans 2 and 3.
- [Visualization Web App For Generated Shapes](./2026-08/11-shape-viewer-webapp/plan.md)
  — approved 2026-08-11: OP-201…OP-205 all accepted (OP-201 amended: Astro
  SSR + islands only, astro-huge-doc reused wholesale, no SPA fallback;
  OP-204 amended: explicit regeneration contract with `seq`/latest-wins
  debouncing and single-changed-parameter support, WASM rejected outright).
  Implementation not started; Phase 1 materializes `package.json`. Depends
  on Plan 1's GLB/SVG exports and the shared parameter-schema contract.
- [Airfoil Parametric Visualizer](./2026-08/11-airfoil-parametric-visualizer/plan.md)
  — approved 2026-08-11: OP-301…OP-305 all accepted (OP-301: NACA 4-digit
  only, Bezier rejected; OP-302: custom numpy only, aerosandbox excluded;
  OP-303: geometry only, no aero feedback in-packet; OP-304: client-side
  inline-SVG plot from generator coords JSON; OP-305 amended: both
  build123d and CadQuery lofts user-switchable, no approximation paths,
  latency accepted via spinner). Excluded ideas captured in the packet's
  `exploration.md`. A second maintainer pass is planned once the Plan 2
  web app is implemented. Implementation gated on Plans 1 and 2.
