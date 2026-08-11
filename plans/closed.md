# Closed Plans

Completed plan packets. Work is implemented and proven (or, for
planning-only packets, the decisions are settled). See each folder for
details.

| Plan | Date | Summary | Proof / Notes |
| --- | --- | --- | --- |
| [CAD Generators Python Environment Bringup](./2026-08/11-cad-generators-bringup/plan.md) | 2026-08-11 | uv environment with four backends (shapely, CadQuery, build123d, OpenSCAD) behind exchange-format contracts; `cadctx` CLI + side-effect-free Python API; `.cache/` output layout (OP-108); OpenSCAD binary provisioned from `config/artifacts.yaml`. Five specs folded. | [test.md](./2026-08/11-cad-generators-bringup/test.md): 50 pytest passed, ruff clean, SVG/DXF/STEP/STL/GLB all written and re-measured, cross-backend volume deviation 0.0018% (tolerance 1%). Log: [implementation.md](./2026-08/11-cad-generators-bringup/implementation.md). |
