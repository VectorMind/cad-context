# Parameter Schema

The contract by which a parametric generator declares its parameters, so any
consumer — a CLI caller, an agent, the companion web app — can drive it without
knowing its internals.

## Declaration

A generator declares parameters as a pydantic model deriving from
`ShapeParams`. Each field carries a default, a range, a step, a unit and a
one-line description. Models reject unknown fields and validate on assignment,
so an out-of-range or misspelled parameter fails at the boundary with a clear
message rather than producing wrong geometry.

Parameter names are lowercase `snake_case` and describe the feature, not the
implementation (`hole_diameter`, not `d1`).

## Transport Form

`cadctx schema <generator>` and `cad_context.api.schema(...)` publish the
declaration as JSON:

```json
{
  "generator": "bracket-cadquery",
  "title": "Flanged bracket (CadQuery)",
  "kind": "3d",
  "backend": "cadquery",
  "formats": ["step", "stl", "glb"],
  "description": "…",
  "parameters": [
    {
      "name": "width",
      "type": "number",
      "default": 80.0,
      "minimum": 20.0,
      "maximum": 300.0,
      "step": 1.0,
      "unit": "mm",
      "options": null,
      "control": "slider",
      "description": "Overall X width of both plates"
    }
  ]
}
```

Every parameter object carries all of `name`, `type`, `default`, `minimum`,
`maximum`, `step`, `unit`, `options`, `control`, `description`; unused entries
are `null` rather than absent, so consumers can index them unconditionally.

- `type` is one of `number`, `integer`, `string`, `boolean`.
- `control` is a rendering hint (`slider`, `select`, `input`). A consumer may
  ignore it, but a numeric parameter always carries a usable range and step so
  a control can be rendered from the schema alone.
- `options` lists the permitted values for an enumerated parameter.

## Consuming The Schema

- Defaults alone must produce a valid shape: every generator is runnable with
  no parameters supplied.
- A consumer sends the **full** parameter set on every generation request;
  partial sets are resolved against the declared defaults before use.
- The schema is the only place parameter metadata is defined. Ranges, units and
  descriptions are never duplicated in a UI, in documentation, or in a second
  schema file — they are read from the generator.
- A consumer may expose only part of the declaration. Publishing a generator's
  parameters is a deliberate choice, not an automatic consequence of declaring
  them: see the curated-exposure rule in
  `specifications/web-app/spec.md`. Such a selection lists parameter *names*
  only and resolves everything else from this schema.

## Generator Identity

A generator is addressed by a stable id (`plate2d`, `bracket-cadquery`). The id
also determines the fixed artifact paths defined in
`specifications/workspace-layout/spec.md`, so a consumer that knows the id can
predict where the geometry will be without parsing a response.
