# Specifications

Use this directory for durable, spec-driven requirements.

Create one folder per specification:

```text
specifications/<slug>/spec.md
```

Specifications should describe the problem, intended behavior, constraints,
interfaces, acceptance criteria, and non-goals. Keep implementation schedules
and running notes in `plans/` instead.

## Current Specifications

- [`workspace-layout/`](workspace-layout/spec.md) — the single `.cache/` output
  root, the per-command result files, console quietness, fixed geometry paths,
  and the rule that in-memory work writes nothing.
- [`agent-interface/`](agent-interface/spec.md) — the `cadctx` CLI as the single
  documented interface for humans and agents, no skills, documentation-based
  routing, and the side-effect-free Python API as the second surface.
- [`exchange-formats/`](exchange-formats/spec.md) — which formats each generator
  backend must emit (STEP, STL, glTF/GLB, SVG, DXF), units, coordinate
  conventions, tessellation quality, and the measurement rules that make an
  export count as proven.
- [`parameter-schema/`](parameter-schema/spec.md) — the contract by which a
  parametric generator declares its parameters (names, types, ranges, defaults)
  so a consumer can render controls for any generator without knowing its
  internals.
- [`web-app/`](web-app/spec.md) — the preview web app: SSR handlers calling the
  CLI as the only geometry source, curated parameter exposure, the regeneration
  contract (full params, `changed`, `seq`, one request in flight, latest-wins),
  and how artifacts are served.
- [`external-binaries/`](external-binaries/spec.md) — external tools declared in
  `config/artifacts.yaml`, provisioned by `cadctx fetch` into `.tools/`, and
  degrading gracefully when absent.
