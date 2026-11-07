# Validation

Fixtures: temporary project roots at two locations; strict manifests; a project
initializer that raises if imported; missing root/project; invalid manifest;
ambiguous candidates; traversal/absolute paths. Developer catalog is isolated
in tests so the real model code and artifacts are never used by test cases.

- Required startup `uv run cadcon info`, `generators`, `paths`: successful before
  changes; four built-ins, no active selection; optional OpenSCAD absent.
- Final `uv run pytest -o addopts= -q --tb=short`: 127 passed, two existing
  optional/platform skips in 10.34 seconds, including isolated collection.
- `uv run ruff check .`: all checks passed.
- Native `uv run cadcon --json project list`: animal-puzzle available and default,
  resolves the existing home-relative Drive root; one initialized project found.
- `uv run cadcon project info`: animal-puzzle selected without explicit options.
- `uv run cadcon --project animal-puzzle generators`: eight entries, comprising
  four built-ins and four approved rounded-bear generators.
- `uv run cadcon --no-project project info`: repository mode as expected.

No geometry implementation changed; geometry verification is not repeated.
Web implementation unchanged; server continues to snapshot one resolved project.
Different physical Drive installations are represented by temporary root
relocation fixtures, not a second machine or remote Drive synchronization test.
