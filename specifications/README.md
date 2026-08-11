# Specifications

Use this directory for durable, spec-driven requirements.

Create one folder per specification:

```text
specifications/<slug>/spec.md
```

Specifications should describe the problem, intended behavior, constraints,
interfaces, acceptance criteria, and non-goals. Keep implementation schedules
and running notes in `plans/` instead.

Expected early specifications for this repository (created once the matching
plan decisions are accepted, not before):

- `exchange-formats/` — which formats each generator backend must emit
  (STEP, STL, glTF/GLB, SVG, DXF), units, and coordinate conventions;
- `parameter-schema/` — the contract by which a parametric generator
  declares its parameters (names, types, ranges, defaults) so the web app
  can render controls for any generator without knowing its internals.
