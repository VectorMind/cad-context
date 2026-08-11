# Closed Plans

Completed plan packets. Work is implemented and proven (or, for
planning-only packets, the decisions are settled). See each folder for
details.

| Plan | Date | Summary | Proof / Notes |
| --- | --- | --- | --- |
| [Visualization Web App For Generated Shapes](./2026-08/11-shape-viewer-webapp/plan.md) | 2026-08-11 | Astro SSR + React islands under `webapp/`: GLB/STL viewer (react-three-fiber + drei), SVG pan/zoom viewer, leva panel rendered from the parameter schema, and the regeneration contract (full params + `changed` + `seq`, one request in flight, latest-wins). SSR handlers call `cadctx`; nothing about geometry is reimplemented. OP-206 (curated parameter exposure) and OP-207 (`cadctx web`) raised and accepted during implementation; `specifications/web-app/spec.md` folded. | [test.md](./2026-08/11-shape-viewer-webapp/test.md): `pnpm build`/`check`/`test` clean, 53 pytest + ruff green, GLB served over HTTP measured at the requested bounds, 40-move slider drag → 2 generations (19 coalesced, 0 stale), regeneration 0.36 s (2D) to 3.5 s (build123d) with an OP-204 (a)→(b) go/no-go note. Log: [implementation.md](./2026-08/11-shape-viewer-webapp/implementation.md). |
| [CAD Generators Python Environment Bringup](./2026-08/11-cad-generators-bringup/plan.md) | 2026-08-11 | uv environment with four backends (shapely, CadQuery, build123d, OpenSCAD) behind exchange-format contracts; `cadctx` CLI + side-effect-free Python API; `.cache/` output layout (OP-108); OpenSCAD binary provisioned from `config/artifacts.yaml`. Five specs folded. | [test.md](./2026-08/11-cad-generators-bringup/test.md): 50 pytest passed, ruff clean, SVG/DXF/STEP/STL/GLB all written and re-measured, cross-backend volume deviation 0.0018% (tolerance 1%). Log: [implementation.md](./2026-08/11-cad-generators-bringup/implementation.md). |
