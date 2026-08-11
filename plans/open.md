# Open Plans

Plan packets with work still outstanding. See each folder for details.

- [Visualization Web App For Generated Shapes](./2026-08/11-shape-viewer-webapp/plan.md)
  — approved 2026-08-11: OP-201…OP-205 all accepted (OP-201 amended: Astro
  SSR + islands only, astro-huge-doc reused wholesale, no SPA fallback;
  OP-204 amended: explicit regeneration contract with `seq`/latest-wins
  debouncing and single-changed-parameter support, WASM rejected outright).
  Implementation not started; Phase 1 materializes `package.json`. Its Plan 1
  dependencies are delivered: GLB/SVG exports sit at fixed paths under
  `.cache/cad/<generator>/`, and the parameter-schema contract is published by
  `cadctx schema <generator>` and specified in
  `specifications/parameter-schema/spec.md`.
- [Airfoil Parametric Visualizer](./2026-08/11-airfoil-parametric-visualizer/plan.md)
  — approved 2026-08-11: OP-301…OP-305 all accepted (OP-301: NACA 4-digit
  only, Bezier rejected; OP-302: custom numpy only, aerosandbox excluded;
  OP-303: geometry only, no aero feedback in-packet; OP-304: client-side
  inline-SVG plot from generator coords JSON; OP-305 amended: both
  build123d and CadQuery lofts user-switchable, no approximation paths,
  latency accepted via spinner). Excluded ideas captured in the packet's
  `exploration.md`. A second maintainer pass is planned once the Plan 2
  web app is implemented. Plan 1 is delivered; still gated on Plan 2.
