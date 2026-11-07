# CLI Rename

Approved scope: rename the main CLI to `cadcon` everywhere in repository code,
tests, documentation, and planning records. Keep the `cad_context` Python package
and `cad-context` distribution names. No legacy command alias is required.

Milestones: update the installed entry point and web bridge; update all references;
validate the installed CLI, Python suite, lint, and web check/tests/build.

Dependencies: existing Windows Python environment and web dependencies.
Risks: stale installed entry points or imports; preserve unrelated working changes.
Exit criteria: the new command works, no old-name references remain in maintained
files, and validation results and any gaps are recorded in test.md.

OP-001 — Rename scope: candidates are command-only or all related identifiers.
Proposal: all related identifiers, including `CADCON_COMMAND` and the web bridge
filename. Confidence: high. Status: settled by the user's request for refactoring
everywhere. External consumers must update their command/override configuration.
