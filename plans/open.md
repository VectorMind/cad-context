# Open Plans

Plan packets with work still outstanding. See each folder for details.

- [CAD Generators Python Environment Bringup](./2026-08/11-cad-generators-bringup/plan.md)
  — planning stage; OP-101…OP-107 (Python window, B-rep backends, OpenSCAD
  path, mesh layer, 2D stack, CLI shape, tooling) proposed and awaiting
  maintainer resolution. `pyproject.toml` is materialized from the accepted
  decisions, not before. Unblocks Plans 2 and 3.
- [Visualization Web App For Generated Shapes](./2026-08/11-shape-viewer-webapp/plan.md)
  — planning stage; OP-201…OP-205 (framework, 3D stack, controls UI,
  regeneration bridge, tooling) proposed and awaiting resolution.
  `package.json` follows the decisions. Depends on Plan 1's GLB/SVG exports
  and the shared parameter-schema contract.
- [Airfoil Parametric Visualizer](./2026-08/11-airfoil-parametric-visualizer/plan.md)
  — planning stage; OP-301…OP-305 (parameterization families, airfoil deps,
  aero feedback, 2D rendering, loft backend) proposed and awaiting
  resolution. First driving use case; implementation gated on Plans 1 and 2.
