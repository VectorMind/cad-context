# Project portfolio in cadcon web

Scope: show the active external project's existing portfolio, declared SVG/image
evidence and generated models in the local preview app. Model migration belongs
to the external project. User requested bear parity and portfolio review before elephant.

Milestones: explicit portfolio file declaration and CLI metadata; confined file
route and project review page; tests, web check/build, live visual inspection.
Existing generator artifact confinement remains unchanged. No second server.

OP-001 resolved: manifest explicitly lists portfolio entry and files; no recursive
project-file serving. HTML renders in a sandboxed iframe. Confidence: high.
Risk: path traversal/symlink escape and stale historical status; reject escapes,
label history and keep current evidence above it. Exit: working SVG/model/history
review with tested confinement and documented CLI metadata.
