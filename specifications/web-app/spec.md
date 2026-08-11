# Preview Web App

The companion web app is a **quick preview-and-tweak surface** for generated
geometry: change a parameter, regenerate, see the shape. It is not a CAD viewer
replacement — where a desktop viewer (ocp_vscode, CQ-editor, FreeCAD) is better
for a job, that job stays there.

## The App Owns No Geometry

The app renders exchange-format files and calls the CLI. It never contains a
second implementation of anything the Python side already does:

- Every answer about shapes — the registry, a parameter schema, a generated
  artifact — comes from a `cadctx … --json` subprocess spawned by a server-side
  handler. Client code never spawns anything and never reads the filesystem.
- Geometry is consumed only through the exchange formats: GLB (or STL) for 3D,
  SVG for 2D. No backend-native format and no in-browser geometry kernel — a
  WASM CAD path in the browser is a rejected design, because it would fork the
  geometry code path away from the backends the repository actually ships.
- Parameter metadata (ranges, steps, units, descriptions) is read from the
  schema, never restated in the app.

## Curated Parameter Exposure

A generator's full parameter model is not automatically an API. The app
declares, per generator, the small set of parameter names it exposes:

- Only exposed names may be sent to the regeneration endpoint. Anything else is
  rejected at the boundary, before a subprocess is spawned, along with values
  that violate the schema's type or range.
- Unexposed parameters are served read-only at their declared default, so the
  page still shows the full shape of the model.
- A generator with nothing exposed is previewable but not editable. Exposing a
  knob is a deliberate edit to the app's configuration, not a side effect of
  adding a parameter to a generator.

The exposure list carries names only. It never carries a range, a unit, or a
default — that would duplicate the parameter schema.

## Regeneration Contract

One endpoint drives regeneration, designed so a warm long-lived worker can
replace the per-request subprocess without a client change.

**Request** — `POST /api/generate`:

```json
{ "generator": "bracket-cadquery", "params": { "width": 120 }, "changed": "width", "seq": 7 }
```

- `params` is always the **full** exposed parameter set; the server resolves
  the rest from the generator's defaults. This keeps the subprocess bridge
  stateless.
- `changed` names the single parameter that moved, or is null. A subprocess
  bridge ignores it; a warm worker may use it for incremental regeneration.
- `seq` is a client-side monotonically increasing sequence number, echoed back.

**Response** — `{ "seq", "artifacts", "timings" }`, where `artifacts` maps a
format to a URL and `timings` reports at least total generation milliseconds.
Errors return `{ "seq", "error" }` with a message that names the offending
parameter. A failed generation is a normal response, never a crashed page.

**Client concurrency rule** — at most **one request in flight**. Further
changes while one is running collapse into a single pending request holding the
latest values; it is dispatched when the in-flight request settles. A response
whose `seq` is older than the newest applied one is discarded. Dragging a
slider therefore costs at most one queued generation regardless of how fast it
moves.

**Server concurrency rule** — generation is serialized per generator. Geometry
paths are fixed (`specifications/workspace-layout/spec.md`), so two concurrent
runs of one generator would write the same file; a second client waits instead.

## Artifacts Over HTTP

Generated files are served from the workspace's `.cache/cad/` directory,
resolved from `cadctx paths` rather than hardcoded, and only from inside it.
Because geometry paths are fixed, an artifact URL is stable for a whole
session; freshness is handled by a cache-defeating query and `no-store`, not by
renaming files.

## Starting It

The web app is reached through the CLI like every other capability: one
documented command installs what is missing, verifies the Python side, starts
the server, and reports the URL. There is no second long-lived Python process
to start — a page's "backend" is a `cadctx` invocation per request. The dev
server's own output is a long log: it goes to `.cache/reports/`, not to the
console.
