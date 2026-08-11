# Test Proof — Airfoil Parametric Visualizer

Environment: Windows 11, Python 3.12.13, `uv sync --extra all` (shapely,
CadQuery, build123d, OpenSCAD, trimesh all available), Node 22 / pnpm for the
web app. All commands run from the repository root.

## Planning-Stage Checks (2026-08-11)

- `plan.md` follows the WORKFLOW.md plan shape: yes.
- Every selecting open point (OP-301…OP-305) lists candidate options, a
  proposal, a confidence level, and a status: yes.
- Sequencing after Plans 1 and 2 and the exact cross-plan dependencies are
  stated explicitly: yes.
- Non-goals separate geometry scope from aerodynamic analysis scope, with
  the analysis question held as an open point (OP-303) rather than silent
  scope creep: yes.

## Suites

| Command | Expected | Actual |
| --- | --- | --- |
| `uv run pytest` | all green | **79 passed** in 17.0 s (50 before Plan 1's close, 53 after Plan 2, 26 added here) |
| `uv run ruff check .` | clean | `All checks passed!` |
| `pnpm --dir webapp check` | 0 errors | `Result (23 files): 0 errors, 0 warnings, 0 hints` |
| `pnpm --dir webapp build` | succeeds | `Server built in 9.12s · Complete!` |
| `pnpm --dir webapp test` | all green | **10 pass, 0 fail** (3 scheduler + 7 new plot-math) |

## Phase 1 — Profile Against Published Ordinates

The exit criterion is that coordinates match published references, so the
profile is checked against Abbott & von Doenhoff's tables rather than against
itself. The tables are the fixtures at the top of `tests/test_airfoil.py`; the
deviations below were read off a throwaway scratch script and are re-asserted
by `test_naca_0012_matches_the_published_thickness_table` and
`test_naca_2412_matches_the_published_surface_table`
(`uv run pytest tests/test_airfoil.py -k naca`).

| Check | Expected | Actual |
| --- | --- | --- |
| NACA 0012 half-thickness at 18 published stations (open TE) | within the table's own rounding, ±0.001% chord | max deviation **0.00054% chord** |
| NACA 2412 upper surface, resampled onto the table stations | < 0.05% chord | max **0.010% chord** |
| NACA 2412 lower surface | < 0.05% chord | max **0.032% chord** (at the 95% station, where the published −0.45 differs from the formula's −0.482) |
| Camber peak of a 2412 | 2.0% chord at 40% chord, zero slope | exact |
| Maximum-thickness station, both TE variants | ≈ 0.30 | 0.29983 (open), 0.29953 (closed) |

The leading-edge station is excluded from the 2412 comparison: the published
table collapses both surfaces to a single 0 there, while the exact
normal-offset construction has no single station at the nose.

### Area — polygon versus the continuous limit

`airfoil_area` (shoelace of the generated polygon) against
`airfoil_continuous_area` (Gauss–Legendre on the exact ribbon integral, after
the `x = ξ²` substitution). Second-order convergence expected; the polygon is
inscribed so it must always undershoot.

| stations/surface | polygon (mm²) | continuous (mm²) | relative error |
| --- | --- | --- | --- |
| 30 | 1175.278735 | 1177.595210 | 1.97e-3 |
| 90 (default) | 1177.349093 | 1177.595210 | 2.09e-4 |
| 300 | 1177.573403 | 1177.595210 | 1.85e-5 |

Ratio 30→90 is 9.4× and 90→300 is 11.3×, i.e. second order as tripling
predicts. Independent cross-check: with no camber the quadrature collapses onto
the closed-form polynomial integral (`0.685083…·t·c²` for the open TE) — they
agree to 1e-12, so neither reference is calibrated to the other.

### Two findings the tests surfaced

1. **The outline reaches ahead of the datum.** For a cambered profile the
   minimum x of the polygon is negative — −0.0115 mm at chord 150, thickness
   15% (−7.6e-5 chord). Real geometry: near the nose `y_t ∝ √x` outruns the
   station, so the normal offset carries the upper surface in front of the
   origin. Pinned by
   `test_cambered_nose_reaches_just_ahead_of_the_chord_line_origin`, and the
   exchange-formats spec was folded to the declared-datum rule behind it.
2. **The family's true peak thickness is 1.0001·t.** The maximum-thickness
   marker spans 14.4017 mm on a 120 mm chord at a nominal 12%, i.e. 12.0014%.
   The NACA polynomial peaks marginally above the thickness it is named for.

## Phase 2 — Loft, Both Backends

Swept with a throwaway scratch script over both kernels; defaults except where
stated (chord 120, span 300, taper 0.6, sweep 15°, 90 stations/surface). The
zero-twist and zero-sweep rows are re-asserted by
`test_wing_loft_matches_the_analytic_volume_without_twist` and
`test_sweep_is_a_shear_and_does_not_change_the_volume`, and the twisted case by
`test_wing_backends_agree_with_each_other_even_when_twisted`.

| Case | Analytic (mm³) | build123d | dev. | CadQuery | dev. |
| --- | --- | --- | --- | --- | --- |
| twist 0 | 230760.4222 | 230760.4222 | 2.4e-15 | 230760.4222 | 2.4e-15 |
| twist 0, taper 1, sweep 0 | 353204.7278 | 353204.7278 | 2.5e-15 | 353204.7278 | 2.5e-15 |
| twist 0, sweep 30° | 230760.4222 | 230760.4222 | 2.3e-15 | 230760.4222 | 2.3e-15 |
| twist 0, open TE | 232185.1787 | 232185.1787 | 3.1e-15 | 232185.1787 | 3.1e-15 |
| twist −3° (default) | 230760.4222 | 230663.6112 | 4.2e-4 | 230663.6112 | 4.2e-4 |
| twist −15° | 230760.4222 | 234482.6837 | 1.6e-2 | 234482.6837 | 1.6e-2 |

Expected and confirmed: the closed form is **exact** at zero twist (a ruled
loft between homothetic sections *is* that solid), sweep is a shear and changes
nothing, and twist costs a term of second order in the angle — 3° → 4.2e-4 and
15° → 1.6e-2 is the 25× the square predicts. Where the closed form loses
exactness the two kernels still agree with each other **bit for bit**, which is
what the cross-backend criterion actually asks.

```
uv run cadctx compare --family wing -p twist=0 --tolerance 0.000001
  → ok · max deviation 0.0000% vs analytic (tolerance 0.0%)
uv run cadctx compare --family wing -p twist=-9
  → ok · max deviation 0.4298% vs analytic (tolerance 1.0%); both backends 2.318e+05
```

Loft construction cost (kernel only, 90 stations/surface): build123d 0.11–0.19 s,
CadQuery 0.04–0.14 s; 300 stations 0.81 s in build123d, still exact to 1.1e-15.

### Exports

`uv run cadctx generate wing-build123d` / `wing-cadquery`, defaults:

- STEP re-imported through a kernel: volume within 1e-6 of the kernel volume
  (`test_wing_exports_round_trip`).
- STL/GLB loaded back: **watertight**, mesh volume within 1% of the analytic
  reference.
- Artifact sizes — build123d: STEP 759 509 B, STL 35 484 B (binary), GLB
  13 748 B. CadQuery: STEP 759 571 B, STL 73 784 B (ASCII), GLB 13 744 B. The
  STL size difference is each kernel's default encoding, not a geometry
  difference; the measured volumes match.

`uv run cadctx generate airfoil`, defaults, measurements from
`.cache/results/generate-airfoil.json`:

```
dxf : 1 polyline, 178 vertices, bounds [0, -5.0838, 120, 9.5040], units mm
svg : 4200 bytes, 1 path, viewBox present
json: 6172 bytes, 3 curves, 270 points, 2 markers, units mm
```

Areas agree to 1e-9 between shapely and the shoelace reference, and to 2e-4
against the continuous limit at the default resolution.

## Phase 3 — The Web Page

Served with `uv run cadctx web --port 4399`; measured with curl against the
running app.

| Request | Result |
| --- | --- |
| `GET /` | 200 |
| `GET /airfoil` | 200 |
| `GET /api/schema/airfoil.json` | the 5 exposed knobs with ranges/steps/units read from the generator; `preview: "json"` |
| `GET /api/artifact/airfoil/airfoil.json` | 200, `content-type: application/json`, 6307 B |
| `GET /api/artifact/wing-cadquery/wing-cadquery.glb` | 200, `content-type: model/gltf-binary`, 25 028 B |

Regeneration through the bridge, warm:

| Generator | Round trip | Note |
| --- | --- | --- |
| `airfoil` | 586–603 ms (5 runs) | drives the 2D plot |
| `wing-cadquery` | 3790, 4549 ms | |
| `wing-build123d` | 6067, 6076 ms | heavier kernel import |

Both wing backends returned volume **230663.6112** for identical parameters
through the app — the backend selector renders two real implementations of the
same specification, not one plus an approximation. Latency is answered by the
spinner, per the OP-305 amendment.

Parameter changes are routed per generator: a `thickness` change regenerated
both shapes (`NACA 2410 → 2416` reported back at 588–965 ms each), a `twist`
change only the loft.

The exposure boundary rejects before spawning anything:

```
{"points":300}            → parameter "points" is not editable for airfoil
                             (editable: chord, max_camber, camber_position,
                              thickness, trailing_edge)
{"taper":5}               → parameter "taper" is above its maximum 1
{"trailing_edge":"blunt"} → parameter "trailing_edge" must be one of open, closed
```

### Plot math, without a browser

`webapp/test/profile.test.js` drives `src/components/profile.ts` directly —
7 tests, all passing:

- a closed curve becomes one `M`, `L`s and a `Z`; an empty curve draws nothing;
- the zoom-1 frame matches the element aspect exactly, so
  `preserveAspectRatio="none"` cannot distort the profile;
- the viewBox flips Y and contains the whole profile at zoom 1;
- dragging moves the plot by exactly the dragged pixel distance, in both axes,
  without changing scale;
- the wheel scales about the pointer with the millimetre under it pinned to
  1e-9, and zooming back out returns to the identity view;
- zoom is clamped to [0.3, 80] under 200 saturating scrolls each way;
- a longer chord reframes the plot around the new profile while keeping the
  zoom factor.

## Known Gaps

- **No automated visual check of the rendered plot.** No headless browser is
  installed in this environment, so the SVG output is proven through its
  coordinate math and the payload contract, not through a screenshot. The page
  itself was exercised over HTTP (200s, artifact content types, regeneration
  round trips) but the pixels were not asserted.
- **The 40-move slider-drag coalescing count was not re-measured here.** The
  scheduler is unchanged from Plan 2 and its rules are covered by
  `test/regeneration.test.js`; the airfoil page instantiates two of them and
  the per-generator dispatch is proven only by the routing behaviour observed
  above.
- **No geometric validity gate on extreme parameters.** Schema ranges bound the
  inputs and `metrics.valid` reports a self-intersecting profile, but nothing
  rejects one.
- Twist-related loft deviation from the closed form is characterised, not
  eliminated; outside twist = 0 the reference is cross-backend agreement.
