Progress: [███] 3/3 — discovery, portable config and native migration complete.

New manifests carry `tool: cadcon`; discovery requires that explicit marker and
a valid schema. Registered legacy projects remain compatible. Added a regression
fixture containing characters-generation, invalid marked and malformed projects.

Added requested personal Drive candidate, separate shared-models root retaining
animal-puzzle as default, and airfoil-wing/reference-parts IDs. Bound models on
this machine to the personal Drive folder. Both external projects own snapshots
of builders, parameters/analytic references and NACA math, plus original cached
exports in evidence, portfolios and fresh verified default CAD exports. Built-in
generators remain reusable and may recreate disposable caches on future use.

Migration scripts are in .cache/scratch; external files were initialized by
`cadcon project init`, then populated without overwriting existing work. Original
12 cache files have SHA-256 inventories; removal follows comparison and successful
CLI verification. Model-specific packets and proof records live externally.

Commands: required startup checks; project init/root; four project verifies;
`uv run pytest -o addopts= -q --tb=short` (128 passed, 2 skips); Ruff repo clean;
external source Ruff fixed import order only. No geometry algorithm changes.
