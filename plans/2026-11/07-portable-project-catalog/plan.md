# Portable project catalog

Approved scope: make the animal puzzle visible by default through versioned
configuration and support different local Drive locations on different machines.

Milestones: implement strict portable catalog and local root binding; add CLI ID
selection and manifest-only discovery; document contracts; validate with isolated
fixtures and the real local project. No geometry or external project edits.

Dependencies: existing project manifests, active pointer and web snapshot flow.
Risks: unavailable Drive roots, accidental developer-project test imports, stale
absolute pointers. Preserve explicit override behavior and isolate test catalogs.
Exit: default resolves locally; relocation and missing-root behavior tested;
project listing does not execute code; full Python tests and Ruff pass.

OP-001 — Storage identity. Candidates: absolute committed path, Drive API identity,
root alias plus relative project path. Proposal: root alias, environment/local
binding and home-relative candidate. Confidence: high. Status: settled, implemented.

OP-002 — Missing default. Candidates: silently use built-ins, actionable error.
Proposal: error, retain `--no-project` escape and working list/root commands.
Confidence: high. Status: settled, implemented.
