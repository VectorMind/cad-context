# Plan: native Windows 3MF export

Date: 2026-11-01. Status: implementation complete; native Windows acceptance passed.
User requested a handoff plan to leave Fusion and use native Windows cad-context. This packet covers only the generic workbench dependency. Model-specific migration documentation remains in the external project's HANDOFF-CADCTX.md.

## Scope

Implement specifications/3mf-export/spec.md through existing documented generate/verify commands, using build123d Mesher and the existing lib3mf dependency. No alternate CAD backend, Fusion integration, package upgrade by default, slicer automation, or new server.

Create implementation.md only when implementation starts, with a filled/empty-block Progress line. Maintain plan/test evidence and fold the delivered format contract into exchange-formats/spec.md and applicable backend/agent-interface documentation in the same pass.

## Milestones

1. Prove native Windows uv/Python execution and run required info/generators/paths. Install locked default extras if missing; preserve Windows .venv. Explicit uv path found: C:\Users\wassi\.local\bin\uv.exe. Use uv run --extra default for subsequent commands.
2. Inspect locked Mesher API and smoke-test export/read of an asymmetric primitive with explicit mm units. Keep scratch in .cache/scratch; use explicit exchange.export for geometry files once supported. Do not introduce standalone production export scripts.
3. Wire format validation/dispatch, single-solid precondition, atomic writer, actual 3MF re-read and measurements. Retain existing format behavior. Inspect registry/project/schema surfaces for all format allow-lists.
4. Extend verify to distinguish required missing artifacts from legitimate optional skips, and to fail invalid object counts/topology/units. Do not count checks on an accompanying STL as 3MF proof.
5. Add meaningful tests and README examples using the actual CLI syntax. Update durable contracts. Include a temporary external-project fixture to prove routing and one-file-per-piece behavior without animal-specific core fixtures.
6. Run native pytest and ruff; run web checks/tests/build only if web sources change. Record actual results. Leave changes in the working tree; no git mutations.

## Open points resolved

| ID | Candidates | Proposal | Confidence | Status |
| --- | --- | --- | --- | --- |
| OP-301 | Mesher / direct lib3mf / external converter | Existing build123d Mesher wrapper; direct lib3mf only for a proven wrapper limitation | High | Resolved |
| OP-302 | New dependency / locked dependency | Existing lock has build123d 0.11.1 and lib3mf 2.5.0 | High | Resolved; native Windows runtime confirmed |
| OP-303 | New command / existing export format | Extend generate/verify and README together | High | Resolved |
| OP-304 | Assembly 3MF / single-piece contract | Initial implementation accepts one solid per artifact | High | Resolved |
| OP-305 | Slicer-specific / generic 3MF | Geometry-only standard 3MF, no print profile | High | Resolved |
| OP-306 | General auto-repair / explicit failure | Fail bad topology; investigate cause | High | Resolved |

## Risks, dependencies and exit criteria

Risks: Windows DLL loading, wrapper-version drift, compound flattening, malformed package references, silently removed optional dependencies and verify reporting success for skipped required formats.
Dependencies: native Windows process execution and locked default extras; no new external executable is planned.
Exit: native CLI produces and verifies a standards-readable single-piece 3MF with actual package/mesh measurements; negative tests fail as intended; all existing checks pass; documentation describes the shipped capability.

No user choice is needed for this technical scope. The implementing agent must obtain concrete runtime evidence, not ask the user to choose an exporter again.

## Completion

All six milestones completed on 2026-11-01. Native Windows 3MF export/read,
16/16 CLI 3MF verification checks, all four built-in verifications, 103 pytest
passes (one optional OpenSCAD skip), and clean Ruff are recorded in test.md.
Implementation decisions and environment recovery are in implementation.md.
`verify` now shares generate's repeated --format/-f selection so opt-in 3MF can
be verified without changing built-in defaults. Existing generic web download
handling needed no source changes. No unresolved open points remain.
