# Open Plans

Plan packets with work still outstanding. See each folder for details.

- [Airfoil Parametric Visualizer](./2026-08/11-airfoil-parametric-visualizer/plan.md)
  — approved 2026-08-11: OP-301…OP-305 all accepted (OP-301: NACA 4-digit
  only, Bezier rejected; OP-302: custom numpy only, aerosandbox excluded;
  OP-303: geometry only, no aero feedback in-packet; OP-304: client-side
  inline-SVG plot from generator coords JSON; OP-305 amended: both
  build123d and CadQuery lofts user-switchable, no approximation paths,
  latency accepted via spinner). Excluded ideas captured in the packet's
  `exploration.md`. Both dependencies are now delivered: Plan 1 (generators,
  exchange formats, parameter schema) and Plan 2 (the web app — viewer pages,
  curated parameter exposure, the regeneration contract). The planned second
  maintainer pass can happen against the running app; note that regeneration
  currently costs 2.3–3.5 s per B-rep shape (Plan 2's `test.md`), which is the
  measured case for escalating OP-204 to a warm worker.
