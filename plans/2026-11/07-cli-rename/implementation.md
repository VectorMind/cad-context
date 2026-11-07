Progress: [■■■] Rename implemented and validated.

Updated the console entry point, web bridge filename/imports/functions/types,
launcher override (`CADCON_COMMAND`), user-facing messages, internal prefixes,
and all documentation/planning references. Python package/distribution names
remain unchanged. Existing working-tree edits were preserved.

Performed startup discovery, inspected the interface spec and web launcher, and
applied a UTF-8 text replacement to versioned and unignored repository files.
No compatibility alias was added. No deviations or unresolved choices.

Refreshed the editable installation with `uv run cadcon --help` using the
existing user cache through approved escalation. Discovery, 2D/3D verification,
Python tests, lint, web check/tests/build, and actual web bridge calls all pass.
Documented launcher override and retained Python names in durable specs.
Validation needed a repository-local pytest temporary directory and disabled
Astro telemetry due to sandbox filesystem restrictions; no product changes were
needed for these environment limitations. See test.md for evidence and commands.
