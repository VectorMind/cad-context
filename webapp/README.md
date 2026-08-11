# cad-context webapp

A quick preview-and-tweak surface for the shapes `cadctx` generates: pick a
generator, move a few sliders, watch the geometry regenerate. Astro SSR +
React islands; three.js for 3D, inline SVG for 2D.

It is not a CAD viewer replacement — for deep inspection use ocp_vscode,
CQ-editor or FreeCAD. The contract behind this app is
[`specifications/web-app/spec.md`](../specifications/web-app/spec.md).

## Run It

From the repository root, one command does everything:

```bash
uv run cadctx web            # installs deps if needed, starts the server, prints the URL
uv run cadctx web --port 4400 --open
```

There is no separate Python server to start. Each page's backend is an SSR
handler that runs `uv run cadctx … --json` as a subprocess, so the Python side
is "running" in the sense that matters: the same CLI, the same `.cache/`, the
same fixed artifact paths.

Node ≥ 22 and pnpm are required. Working inside `webapp/` directly also works:

```bash
pnpm install
pnpm dev          # http://localhost:4321
pnpm build        # production build (SSR, node standalone)
pnpm check        # astro check / TypeScript
pnpm test         # the regeneration scheduler's rules
```

## What A Page Does

```
browser ──POST /api/generate──▶ Astro SSR handler ──▶ uv run cadctx generate … --json
   ▲                                                             │
   └───── GET /api/artifact/<generator>/<file> ◀── .cache/cad/ ◀──┘
```

1. The page is rendered on the server from `cadctx schema <generator>`, filtered
   to the exposed knobs.
2. On mount the island asks for one generation with the defaults.
3. Every slider change goes through the scheduler: one request in flight,
   intermediate values coalesced, stale responses discarded.
4. The response carries the artifact URL; the viewer reloads just that file.

## Choosing Which Parameters Are Editable

The API is deliberately narrow. `config/exposure.json` lists, per generator,
the parameter *names* that may be edited:

```jsonc
{
  "generators": {
    "plate2d": { "editable": ["width", "slot_count", "slot_width"], "preview": "svg" },
    "bracket-cadquery": { "editable": ["width", "height", "hole_diameter"], "preview": "glb" }
  }
}
```

- Only these names are accepted by `POST /api/generate`; anything else is
  rejected before a subprocess starts.
- Everything else is shown read-only at its generator default (the "fixed"
  section of the panel).
- No ranges, units or defaults live here — those are read from the generator's
  schema. Adding a knob is one word.

## API

| Route | Purpose |
| --- | --- |
| `GET /api/generators.json` | every generator with the knobs it exposes |
| `GET /api/schema/<generator>.json` | the editable contract + the fixed parameters |
| `POST /api/generate` | `{ generator, params, changed?, seq }` → `{ seq, artifacts, timings }` |
| `GET /api/artifact/<generator>/<file>` | the generated file from `.cache/cad/` |

```bash
curl -s localhost:4321/api/schema/plate2d.json
curl -s -X POST localhost:4321/api/generate \
  -H 'content-type: application/json' \
  -d '{"generator":"plate2d","params":{"width":160,"slot_count":5,"slot_width":12},"seq":1}'
```

## Layout

```text
config/exposure.json          which parameters this app exposes
src/server/cadctx.ts          the subprocess bridge (the only place that spawns)
src/server/exposure.ts        filtering + validation against the schema
src/pages/                    index, /viewer/<generator>, /api/*
src/components/regeneration.ts  the scheduler (one in flight, latest-wins)
src/components/ShapeWorkbench.tsx  the island: leva panel + viewer + status
src/components/ModelView.tsx  GLB/STL via react-three-fiber + drei
src/components/SvgView.tsx    inline SVG with pan/zoom
test/regeneration.test.js     proof of the client concurrency rules
```

## Notes

- Exports are millimetre, Z-up CAD coordinates; the 3D view rotates the model
  into three.js's Y-up world.
- The camera fits the part on first load and on **fit view**; a regenerated
  part only rescales the distance, so an orbit survives a parameter change.
- Artifact URLs carry a cache-busting query because the underlying geometry
  path is fixed by contract and rewritten in place.
