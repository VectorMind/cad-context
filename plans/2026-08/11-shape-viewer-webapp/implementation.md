# Implementation Log — Visualization Web App For Generated Shapes

## Progress

`▰▰▰▰▰▰ Done`
Phases 1–5 landed: scaffold, static viewers, parameter panel, regeneration
loop and measured proof; follow-ups at the end are non-blocking.

## Files Added

Web app (`webapp/`):

| File | Role |
| --- | --- |
| `package.json`, `pnpm-workspace.yaml`, `astro.config.mjs`, `tsconfig.json` | Astro 5 SSR (node standalone) + React 19 islands, pnpm, strict TypeScript |
| `config/exposure.json` | the curated editable surface: parameter *names* per generator, plus the preview format (OP-206) |
| `src/server/cadctx.ts` | the only place that spawns anything: `uv run cadctx … --json`, memoized registry/schema/layout lookups, per-generator serialization |
| `src/server/exposure.ts` | filters a generator's schema to the exposed knobs and validates incoming values against it |
| `src/pages/index.astro` | generator list, rendered from `cadctx generators` |
| `src/pages/viewer/[generator].astro` | one page per generator; schema resolved server-side, island hydrated `client:only` |
| `src/pages/api/generate.ts` | the regeneration contract endpoint |
| `src/pages/api/artifact/[...file].ts` | serves `.cache/cad/` files, path-guarded, `no-store` |
| `src/pages/api/generators.json.ts`, `src/pages/api/schema/[generator].json.ts` | the app's registry and per-generator editable contract as JSON |
| `src/components/regeneration.ts` | framework-free scheduler: one request in flight, latest-wins coalescing, stale-response discard |
| `src/components/useRegeneration.ts` | the React binding for it |
| `src/components/ShapeWorkbench.tsx` | the island: leva panel from the schema, viewer, status bar, fixed-parameter list, measured metrics |
| `src/components/ModelView.tsx` | GLB/STL through react-three-fiber + drei (OrbitControls, Grid), manual load/dispose, camera framing |
| `src/components/SvgView.tsx` | inline SVG with pan/zoom |
| `src/layout/Layout.astro`, `layout/tokens.css`, `layout/app.css` | shell and design tokens |
| `test/regeneration.test.js` | node:test proof of the client concurrency rules |
| `README.md` | how to run it, the API, how to expose a parameter |

Python side: `src/cad_context/web.py` (locating the app, `pnpm install`,
spawning the dev server, reading back the port it bound, verifying it answers),
the `web` command in `src/cad_context/cli.py`, and `tests/test_web.py`.

Docs and contracts: `specifications/web-app/spec.md` (new), pointers from
`specifications/README.md` and `specifications/parameter-schema/spec.md`, a
"Preview In The Browser" section plus the `cadctx web` entry in `README.md`,
and web-app rules in `AGENTS.md`.

## Implementation Facts

- **The app owns no geometry.** Every shape fact is a `cadctx --json`
  subprocess: `generators`, `schema <id>`, `paths` (memoized for the life of
  the server) and `generate` (never cached). The `.cache/cad/` directory is
  resolved from `cadctx paths`, not hardcoded.
- **Curated exposure (OP-206).** `config/exposure.json` lists 3 editable names
  per generator out of 5 (bracket) or 7 (plate). Unlisted parameters are
  returned read-only at their defaults and are rejected by `POST /api/generate`
  with a message naming the editable set. Type, minimum, maximum and integer
  checks run against the generator's own schema before anything is spawned, so
  the file carries names only.
- **One command (OP-207).** `cadctx web` installs dependencies when
  `node_modules/astro` is missing, probes backends, spawns `pnpm dev`, reads
  the URL back out of the dev server's log (Astro moves to the next free port
  when one is taken), polls until it answers, and only then emits its result
  file. The dev server's output stays in `.cache/reports/web.log`.
- **Regeneration contract.** Request `{ generator, params, changed?, seq }` →
  `{ seq, artifacts, timings, status, params, metrics, notes }` or
  `{ seq, error }`. `changed` is carried and forwarded but unused by the
  subprocess bridge — it exists so a warm worker slots in unchanged.
  Regeneration asks for the preview format only (`-f glb` or `-f svg`) and
  passes `--no-measure`, so a slider costs one export, not five.
- **Two concurrency guards.** The client keeps one request in flight and folds
  intermediate values into a single queued request; the server serializes
  generation per generator, because fixed artifact paths mean two concurrent
  runs would write the same file.
- **Client bundles are split.** `ModelView` and `SvgView` are lazy, so a 2D
  page never downloads three.js: 1.9 kB for the SVG viewer against 937 kB for
  the 3D one.
- **CAD frame in the browser.** GLB from trimesh carries raw millimetre Z-up
  coordinates with no node transform (verified by reading the glTF JSON chunk),
  so the viewer centres the object and rotates it -90° about X into three.js's
  Y-up world.
- **Shading.** The GLB primitives carry `POSITION` and indices only — no
  `NORMAL` attribute — so every face shaded identically and a part rendered as
  one flat silhouette. The viewer now flat-shades any mesh that arrives without
  normals (three derives the true per-face normal in the shader, which is also
  the right look for a faceted CAD part) and keeps a file's normals when it has
  them. Lighting is a three-point rig plus a sky/ground hemisphere, so each
  face picks up a different amount of light.

## Decisions Made During Development

- **astro-huge-doc is reused as a stack and a convention, not copied
  wholesale** — a deviation from OP-201's "full copy reuse". That codebase is a
  Markdown documentation engine (express, better-sqlite3, auth, content
  pipelines, ~60 dependencies); none of it applies to a nine-file preview app,
  and copying it would have imported a second workspace/config system into this
  repository. What is reused: the Astro 5 + `@astrojs/node` + React 19 islands
  stack, pnpm, the single-token-file styling convention, and the layout shell
  shape (appbar + slot).
- **Camera framing keeps the user's orbit.** A full fit runs on the first model
  and on "fit view"; a regenerated part only rescales the camera distance by
  how much the part grew. Refitting on every regeneration fought the user's
  view, and never refitting left a part that tripled in size out of frame.
- **leva controls are transient.** Values are held in a ref and pushed to the
  scheduler; leva does not re-render the page per dragged frame. A 40-step drag
  produced 21 control events and 2 generations.
- **A three-line test surface after all.** OP-205 said no test framework in the
  first pass; the scheduler is the one piece with rules worth proving, so it was
  extracted framework-free and covered by three `node --test` cases. No test
  framework was added — `pnpm test` is Node's own runner over the TypeScript
  source (type stripping), which is also why that file avoids constructor
  parameter properties.

## Deviations From The Plan

- astro-huge-doc reuse is stack-level, not a full copy (above).
- The plan's `package.json` sketch listed no dev dependencies beyond TypeScript
  and `@types/three`; `@astrojs/check`, `@types/node`, `@types/react` and
  `@types/react-dom` were added so `pnpm check` is meaningful. `pnpm-workspace.yaml`
  exists only to let pnpm 10 run the `esbuild`/`sharp` install scripts.
- Prettier was not added (OP-205 named it as a default). Formatting is
  consistent by hand; adding it is a one-line follow-up if it ever drifts.
- The plan spoke of loading artifacts "from `out/`"; Plan 1's OP-108 moved
  geometry to `.cache/cad/`, and the app resolves that from `cadctx paths`.
- `cadctx web` (OP-207) is new surface the plan did not anticipate.

## Follow-Up Risks

- **Subprocess latency is the ceiling.** Steady-state regeneration is ~0.36 s
  (plate2d), ~1.86 s (OpenSCAD), ~2.3 s (CadQuery), ~3.5 s (build123d) —
  dominated by interpreter and OCCT import, not by geometry. This is a preview
  loop, not a live slider. Escalating OP-204 to mode (b) (a warm worker behind
  the same contract) is the fix when that becomes intolerable; see `test.md`
  for the go/no-go note.
- The 3D viewer offers a wireframe toggle, not true B-rep edges — GLB from a
  tessellated mesh has no edge topology. `three-cad-viewer` remains the
  documented answer if edge fidelity becomes a requirement.
- **The exported GLB still has no normals.** The viewer compensates, but any
  other glTF consumer (3dviewer.net, `<model-viewer>`, Blender import) shows
  the same flat surface this app used to. Fixing it at the source is a
  one-argument change in `exchange/export3d.write_glb`
  (`mesh.export(..., include_normals=True)`), but it needs a decision about
  smooth versus per-face normals for a merged-vertex mesh — smooth normals
  would round off the hard edges of a mechanical part. Left untouched here
  because it is an exchange-format change, not a renderer one.
- Only Chromium was exercised (headless, via a throwaway Playwright script in
  the scratchpad). No mobile or Safari pass.
- The app assumes `uv` on PATH; `CADCTX_COMMAND` overrides the launcher for
  environments where `cadctx` is already installed.
- A generator whose backend is missing shows an empty page with the CLI's error
  in the status bar; it is honest but not pretty.

## Commands That Matter

```bash
uv run cadctx web                 # install (first run), preflight, serve, print the URL
uv run cadctx web --port 4400 --open
cd webapp && pnpm build           # production SSR build
cd webapp && pnpm check           # astro check / TypeScript
cd webapp && pnpm test            # regeneration scheduler rules
```
