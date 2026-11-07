# Drive project migration

Scope: add `~/My Drive/Projects/3d-models` as a storage candidate, preserve all
four cached built-in models as external projects, and filter discovery to cadcon
projects. Keep the animal puzzle in its existing shared folder and as default.

Milestones: mark cadcon manifests and filter discovery; configure personal and
shared roots; initialize two external projects with source snapshots and cached
exports; verify their generators; remove original cache copies only after byte
comparison and successful verification. Preserve reusable built-ins in the repo.

Risks: both root candidates exist (bind explicitly); cached exports lack full
parameter metadata (preserve exact original bytes as historical evidence and
generate documented default models separately). Never overwrite existing files.

Exit: valid project listing excludes unrelated folders; all original bytes
preserved; four external generators pass CLI verification; tests and Ruff pass.

OP-001 — Grouping. Proposal: airfoil/wing together, reference plate/bracket
together. Confidence high; settled based on model relationships.
OP-002 — Discovery identity. Proposal: explicit `tool: cadcon` for discovered
projects; registered legacy manifests remain compatible. Confidence high; settled.
