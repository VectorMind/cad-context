# Test Proof — Visualization Web App For Generated Shapes

Environment: Windows 11, Node v22.21.1, pnpm 10.22.0, uv 0.11.19, Python
3.12.13, Astro 5.18.2, three 0.180.0, leva 0.10.1. All five backends
available (`shapely, cadquery, build123d, openscad, trimesh`), OpenSCAD binary
resolved from `.tools/`. The API and browser checks below ran against a server
started with `uv run cadctx web --port 4399`; the startup section repeats the
run on the default port.

## Planning-Stage Checks (2026-08-11)

- `plan.md` follows the WORKFLOW.md plan shape: yes.
- Every framework/tool-selecting open point (OP-201…OP-207) lists candidate
  options, a proposal, a confidence level, and a status: yes.
- External-viewer alternatives (ocp_vscode, CQ-editor, FreeCAD) are
  documented as complements, per the integrate-don't-rebuild rule: yes.
- Dependency on Plan 1's exchange formats and parameter-schema contract is
  stated explicitly: yes.

## Build, Types, Lint, Tests

| Command | Expected | Actual |
| --- | --- | --- |
| `cd webapp && pnpm install` | clean install | 12.2 s, esbuild/sharp build scripts allowed via `pnpm-workspace.yaml` |
| `cd webapp && pnpm build` | SSR build succeeds | `Complete!` — server built in 4.8 s; client chunks `ModelView` 937.01 kB, `ShapeWorkbench` 217.29 kB, `SvgView` 1.88 kB (three.js only loads on 3D pages) |
| `cd webapp && pnpm check` | no type errors | `Result (18 files): 0 errors, 0 warnings, 0 hints` |
| `cd webapp && pnpm test` | scheduler rules hold | 3 passed, 0 failed |
| `uv run pytest` | green, including the three new `tests/test_web.py` cases | 53 passed |
| `uv run ruff check .` | clean | `All checks passed!` |

## Starting Both Halves (OP-207)

`uv run cadctx web` from a clean start (console, verbatim):

```text
ok web — serving http://127.0.0.1:4321/ (5/5 backends ready)
  url: http://127.0.0.1:4321/
  webapp: webapp
  backends_ready: shapely, cadquery, build123d, openscad, trimesh
  backends_missing: none
  generators: http://127.0.0.1:4321/api/generators.json
  note: stop with Ctrl-C; the dev server log is in the report file
  result: .cache/results/web.json
  report: .cache/reports/web.log
```

Immediately afterwards, `POST /api/generate` for `plate2d`
(`width 200, slot_count 6, slot_width 14`) returned
`{"seq":1,"artifacts":{"svg":"/api/artifact/plate2d/plate2d.svg?v=…"},
"timings":{"total_ms":671,"cli_ms":377}}` with
`area 12724.67` against `area_analytic 12724.34`.

Expected: one command installs (if needed), verifies the Python side, starts
the Astro server, prints a URL that answers, and keeps the dev server's own
output out of the console. Actual: as above; `.cache/reports/web.log` holds the
Astro banner and request log; `GET /` answered 200 in 403 ms (cold) / 4 ms
(warm).

## API Contract

| Check | Expected | Actual |
| --- | --- | --- |
| `GET /api/generators.json` | 4 generators, each with its editable names | plate2d, bracket-cadquery, bracket-build123d, bracket-openscad; `editable` present on all four |
| `GET /api/schema/plate2d.json` | 3 editable parameters with ranges from the generator, 4 fixed | `width [40..400] mm`, `slot_count [1..9]`, `slot_width [2..40] mm`; fixed: `height`, `corner_radius`, `slot_length`, `hole_diameter` |
| `POST /api/generate` (plate2d, width 160 / slots 5 / slot_width 12) | `{seq, artifacts, timings}`, SVG regenerated | `seq 1`, `artifacts.svg = /api/artifact/plate2d/plate2d.svg?v=…`, `total_ms 366`, `area 10386.67` vs `area_analytic 10386.48` |
| `POST /api/generate` (bracket-cadquery, width 120 / height 70 / hole 10) | GLB regenerated | `seq 2`, `total_ms 2609`, `volume 87395.044` = `volume_analytic 87395.044` |
| `GET /api/artifact/plate2d/plate2d.svg` | served with the right type | `200`, `content-type: image/svg+xml`, `cache-control: no-store`, 29 257 bytes |
| `GET /api/artifact/bracket-cadquery/bracket-cadquery.glb` | valid GLB | `200`, `model/gltf-binary`, 37 816 bytes, magic `glTF` |
| `GET /api/artifact/plate2d/nope.svg` | 404 with a useful message | `404 no artifact at plate2d/nope.svg — generate it first` |
| `GET /api/artifact/../../../pyproject.toml` (`curl --path-as-is`) | never escapes `.cache/cad/` | `404`; encoded form `..%2f..%2f` also `404` |
| `GET /viewer/nope` | 404 | `404` |

### Curated exposure (OP-206) — rejections before anything is spawned

| Request | Response |
| --- | --- |
| `params: {corner_radius: 12}` on plate2d | `400 {"seq":3,"error":"parameter \"corner_radius\" is not editable for plate2d (editable: width, slot_count, slot_width)"}` |
| `params: {width: 9000}` | `400 … "parameter \"width\" is above its maximum 400"` |
| `params: {slot_count: 2.5}` | `400 … "parameter \"slot_count\" must be an integer, got 2.5"` |
| `generator: "nope"` | `400 … "unknown generator 'nope'; known: plate2d, bracket-cadquery, bracket-build123d, bracket-openscad"` |

## Geometry Round-Trip Through The App

Requested `bracket-cadquery` at `width=200, height=40, hole_diameter=6`, then
downloaded the artifact the response pointed at and parsed the GLB JSON chunk:

```text
artifact url: /api/artifact/bracket-cadquery/bracket-cadquery.glb?v=1786477717176
served GLB bytes: 37816 | magic: glTF
mesh bounds min [0,0,0] | max [200,60,40]
```

Expected: the file served over HTTP is the geometry just requested (width 200,
fixed depth 60, height 40). Actual: exact match. Kernel volume equalled the
analytic volume on every 3D request (e.g. 87395.04440784613 both ways).

## Regeneration Latency (steady state, three runs each)

| Generator | Format | `total_ms` (server) | `cli_ms` |
| --- | --- | --- | --- |
| `plate2d` | SVG | 418 / 370 / 357 | 417 / 369 / 357 |
| `bracket-openscad` | GLB | 1858 / 1872 / 1857 | 1858 / 1871 / 1856 |
| `bracket-cadquery` | GLB | 2297 / 2289 / 2315 | 2297 / 2289 / 2315 |
| `bracket-build123d` | GLB | 3561 / 3473 / 3482 | 3561 / 3472 / 3482 |

`total_ms - cli_ms` is 0–2 ms: the endpoint's own overhead is nil, the cost is
the `uv run cadctx` process (interpreter + OCCT import) plus the export.

**OP-204 (a)→(b) go/no-go.** Mode (a) is *kept* for now. It is comfortable for
2D (~0.36 s feels immediate) and workable for 3D as a preview loop — the
latest-wins client means a drag costs two generations, not forty, so the app
stays responsive even at 3.5 s per shape. It is *not* enough for continuous
slider feedback on B-rep parts. Recommendation: escalate to mode (b) — a warm
worker behind the identical request/response contract — when interactive B-rep
dragging becomes a requirement (Plan 3's airfoil work is the likely trigger).
The measured ceiling to beat is 2.3–3.5 s per regeneration, essentially all of
it process startup.

## Concurrency

**Client (unit, `webapp/test/regeneration.test.js`, 3 passed).**

| Case | Expected | Actual |
| --- | --- | --- |
| burst of five changes | 2 requests, latest value last, never 2 in flight | dispatched 2, coalesced 3, peak in-flight 1, second request carried `width=160` and `changed="width"` |
| response with an older `seq` | discarded, fresh render survives | `discarded 1`, artifacts still the fresh URL |
| transport failure | error surfaced, queue not wedged | error reported, next change still dispatched |

**Client (in-browser, headless Chromium).** Loaded `/viewer/bracket-build123d`,
dragged leva's `width` slider through 40 mouse moves at ~50 Hz:

```json
{ "mouseMovesDuringDrag": 40, "postsBeforeDrag": 1, "postsDuringDrag": 1,
  "postsTotal": 3, "counters": "3 sent · 19 coalesced · 0 stale",
  "width": "300",
  "bodies": [ {"seq":1,"changed":null,"params":{"width":80,…}},
              {"seq":2,"changed":"width","params":{"width":101,…}},
              {"seq":3,"changed":"width","params":{"width":300,…}} ] }
```

Expected: one initial generation plus at most one queued request per drag, the
last one carrying the final slider value. Actual: exactly that — 21 control
events collapsed into 2 generations, the final request carrying `width=300`,
`0 stale`, no console or page errors. Same result on `bracket-cadquery`.

**Server.** Two simultaneous `POST /api/generate` for `bracket-build123d`:
request A returned in 3.549 s (`cli_ms 3541`), request B in 7.003 s
(`cli_ms 3469`). B's own generation time is unchanged while its total includes
A's — proof that generation is serialized per generator, so two browser tabs
cannot write the same fixed artifact path at once.

## Rendering

Headless Chromium (throwaway Playwright script, screenshots kept out of the
repository per the workspace rules):

| Page | Expected | Actual |
| --- | --- | --- |
| `/` | four generator cards with backend, formats and exposed knobs | rendered, links to each viewer |
| `/viewer/plate2d` | inline SVG with pan/zoom, three sliders, measured area | `svg: true`, controls `width (mm), slot_count, slot_width (mm)`, metrics `area, area_analytic, perimeter, rings`, `398 ms round-trip · 391 ms cadctx`, no console errors |
| `/viewer/bracket-build123d` | WebGL canvas with the bracket, orbit controls, grid | `canvas: true`, metrics `volume, volume_analytic, area`, model visible and framed, no console errors |

Camera behaviour checked visually across a regeneration: after dragging width
from 80 mm to 300 mm the part stays framed at the user's orbit angle (distance
rescales, angle preserved); **fit view** re-frames on demand.

## Known Gaps

- Only headless Chromium was exercised; no Safari, Firefox, or touch pass.
- The wireframe toggle is a material flag, not B-rep edges (GLB carries no edge
  topology). No edges/section tooling, as scoped.
- STL is supported by the viewer but every 3D generator previews GLB, so the
  STL path is exercised only by code inspection, not by a served page.
- DXF and STEP are downloadable through the artifact route but have no viewer.
- `.cache/reports/web.log` grows for the life of a server run; it is truncated
  on the next `cadctx web`.
- No load test beyond two concurrent clients.
