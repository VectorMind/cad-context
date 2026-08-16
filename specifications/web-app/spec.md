# Preview Web App

## Role

The web app is a quick preview-and-tweak surface, not a CAD system. It renders
real exchange artifacts and never owns geometry, parameter ranges, defaults, or
backend-native logic.

Every shape answer comes from a server-side `cadctx --json` subprocess:
registry, schema, generation, paths, and artifacts. Client code never spawns a
process or reads the filesystem.

## Curated Exposure

Only explicitly exposed parameter names reach `POST /api/generate`. Built-in
exposure lives in `webapp/config/exposure.json`; project exposure lives in
`project.yaml` and is returned by the CLI registry/schema. Types, ranges, steps,
units, and defaults always come from the parameter model. Unknown, unexposed,
wrong-type, and out-of-range inputs are rejected before generation.

## Regeneration

The request contains generator id, the full exposed parameter set, an optional
changed name, and a monotonic sequence. The response contains artifact URLs,
metrics, status, and timings. The client permits one request in flight and
collapses further changes to the newest pending values. The server serializes
generation per generator because paths are fixed.

No approximate preview replaces a real generator. Latency is represented by a
busy state.

## Projects And Artifacts

`cadctx web` snapshots one active project for the process lifetime. Registry and
schema memoization is therefore safe; switching projects requires restarting
the server. The index groups active-project generators under their project name.

Every registry entry supplies its artifact root. The artifact handler resolves
the requested generator, checks its one filename component, and confines both
lexical and real paths to that generator root. URLs stay stable and responses
use `no-store` plus a cache-defeating query after regeneration.

## Starting

The only supported start surface is `cadctx web`. It resolves dependencies,
starts Astro, passes the snapshotted project environment, writes the server log
under `.cache/reports/`, and prints the URL. There is no separate long-lived
Python service.
