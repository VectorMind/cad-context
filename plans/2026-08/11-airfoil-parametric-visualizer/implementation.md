# Implementation — Airfoil Parametric Visualizer

## Progress

`▰▰▰▰▰ Done` — Phases 0–4 landed and proven; NACA profile, both lofts, the
`/airfoil` page and the spec folds are in the working tree.
Non-blocking follow-up: the wing loft regenerates in ~4–6 s through the
per-request subprocess, which is the OP-204 warm-worker case again.

## What Landed

### Phase 1 — Profile core

- `src/cad_context/airfoil.py` (new): the NACA 4-digit family in numpy — cosine
  stations, thickness distribution, camber line and slope, the normal-offset
  surface construction, the closed outline polygon, shoelace area, the
  maximum-thickness station, and two area references. No CAD kernel, no airfoil
  library (OP-301/OP-302 as accepted).
- `generators/models.py`: `AirfoilParams` and `WingParams` (the latter extends
  the former, so the profile knobs are literally the same fields), plus the
  analytic geometry — `airfoil_outline`, `airfoil_area`,
  `airfoil_continuous_area`, `airfoil_payload`, `wing_sections`, `wing_volume`,
  `wing_bounds`.
- `generators/airfoil2d.py` (new): shapely polygon + payload + metrics.

Two area references rather than one, because they prove different things:

- `airfoil_area` is the shoelace area of the *very polygon* the exporters and
  the loft sections are built from. Kernel-free, and it keeps the
  discretisation visible instead of hiding it inside the reference.
- `airfoil_continuous_area` is the discretisation-free limit. A cambered
  profile is the ribbon of half-width `y_t` laid normal to the camber line, so
  its area is exactly `∫ 2 y_t √(1 + y_c'²) dx` — the curvature corrections of
  the two surfaces cancel over the symmetric width. Substituting `x = ξ²`
  removes the √x branch point and leaves a polynomial integrand on each side of
  the camber break, so Gauss–Legendre reaches machine precision rather than
  merely converging. The polygon converges to it at second order, which is the
  test.

### Phase 2 — Loft

- `generators/wing_build123d.py` and `generators/wing_cadquery.py` (new). Both
  ruled lofts through the *same* section wires: `wing_sections` computes them
  in `models.py`, so neither backend owns any airfoil geometry and the volumes
  are genuinely comparable (the AGENTS multitudes rule).
- Sections are the profile scaled by the local chord, rotated about its own
  quarter-chord by the local twist, and offset by the leading-edge sweep. Root
  and tip only: taper, twist and sweep are all linear in span, so two sections
  define the ruled solid exactly.
- `wing_volume` is a closed form, `A·s·(1 + k + k²)/3`. Every intermediate
  section of a ruled loft between homothetic polygons is that polygon scaled,
  so the spanwise area distribution is quadratic and integrates exactly; sweep
  is a shear and leaves it alone. **Twist does not** — a ruled loft between
  rotated sections loses a term of second order in the angle. Measured: 4.2e-4
  at 3°, 1.6e-2 at 15°, exact (2.4e-15) at 0°. Recorded rather than papered
  over, and the cross-backend check covers the twisted case instead.

### The `json` exchange format

OP-304 needs coordinates in the browser. Rather than smuggle them through
`metrics` (a measurement channel), they became a real exchange format:

- `BuildResult.payload` — backend-neutral plain data, the counterpart to
  `native`. Anything may read it; `native` still nobody may.
- `exchange/export2d.py`: `write_json` (verbatim) and `read_json_metrics` (the
  round-trip measurement the proof obligations require).
- `json` joins `FORMAT_ORDER`; the artifact route serves it as
  `application/json`.

A generator declaring `json` without a payload raises `ValueError`, not
`BackendUnavailable`: that is a wiring bug and must be loud, not degraded away.

### Generator families

A second 3D part broke an assumption `cadctx compare` had been getting away
with — that every 3D generator builds the bracket. `GeneratorSpec.family` makes
the grouping explicit:

- `generators.family(name, kind=...)` / `families()`.
- `cadctx compare --family bracket|wing`, writing `compare-<family>.json` (the
  same shape as `generate-<generator>`), and `api.compare(family=...)`.
- The pytest fixture `generator_3d` became `bracket_3d`, and conftest now
  parametrises any `<family>_3d` fixture. The fixture always *meant* "the
  bracket on each backend"; it just never had to say so.

### Phase 3 — Web page

- `webapp/src/components/ProfileView.tsx`: plain inline SVG, one path per
  curve, plus grid, axis ticks, markers and a legend. No canvas, no charting
  library (OP-304 as resolved).
- `webapp/src/components/profile.ts`: the framing math extracted framework-free
  — the Y flip, the aspect match, pan and zoom — so it is provable without a
  browser (`test/profile.test.js`).
- `webapp/src/components/AirfoilWorkbench.tsx` + `src/pages/airfoil.astro`: one
  leva panel over both schemas, grouped into `profile` and `wing` folders, and
  **two schedulers**. A change is routed only to the generators that declare
  it, so `twist` never re-runs the 2D profile and the 0.6 s redraw never queues
  behind the 4 s loft.
- The backend selector is built from `cadctx generators` filtered to
  `family === 'wing'`, so the page names no backend and a third implementation
  would appear by registering.
- `ShapeWorkbench` gained the `json` preview case, so `/viewer/airfoil` works
  as an ordinary generator page too.
- `config/exposure.json`: the profile knobs and `trailing_edge` for `airfoil`;
  those plus span/taper/twist/sweep for both wings. `points` stays unexposed —
  it is resolution, not shape, and it is what loft cost scales with.

### Decisions Made During Implementation

- **The datum is the camber line's leading edge, not the outline's minimum.**
  The exchange-formats spec said 2D parts sit with "the outline's minimum
  corner at the origin". An airfoil cannot: surface points are offset normal to
  the camber line, and near the nose the thickness (∝ √x) outruns the station,
  so the outline reaches ~8e-5 chord *ahead* of the origin. Measured, pinned by
  a test, and the spec was folded to the durable rule behind it — a part's
  origin is its **declared datum**, stated in its parameter model, identical
  across every format.
- **Two area references, not one** (above): a self-comparison would have been
  no proof at all.
- **`compare` result files are now per family**, matching `generate-` and
  `schema-`; a wing comparison no longer clobbers a bracket one. The README
  reference to `.cache/results/compare.json` was updated.

### Spec Folds

- `specifications/exchange-formats/spec.md`: the declared-datum rule; the JSON
  coordinate payload (shape, meaning, "geometry never travels as a metric");
  its round-trip proof obligation; families as the unit of cross-backend
  agreement, including the rule that where a closed form is exact only over
  part of the parameter space the backends must still agree with each other.
- `specifications/web-app/spec.md`: the OP-305 wisdom-level rule the plan asked
  to fold — multiple real implementations offered as a user switch, no
  approximation paths, latency answered with a busy indicator; plus the rule
  that a plotting page still owns no geometry.
- `AGENTS.md`: family in the add-a-generator checklist, the payload/`json`
  step, and the no-approximation rule under Multitudes.

### Follow-Up Risks

- Regeneration of a wing costs 3.8–6.1 s end to end, nearly all of it `uv run`
  startup plus the OCCT import (the loft itself is ~0.15 s). Accepted by OP-305
  and answered with a spinner, but it is the strongest case yet for the OP-204
  warm-worker escalation.
- Extreme parameter combinations (very high camber with a thin section) are
  bounded by the schema ranges rather than by a geometric validity check; the
  profile's `valid` flag reports self-intersection but nothing rejects it.
