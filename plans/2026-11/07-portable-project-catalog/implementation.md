Progress: [████] 4/4 — catalog, CLI, contracts, validation complete.

Added versioned `config/projects.yaml` with animal-puzzle as default and a `models`
root. Added strict catalog loading, confined resolution, local root binding,
manifest-only discovery, and `project root` / `project list` commands. Existing
selection surfaces accept catalog IDs; ID pointers remain portable. Explicit
paths and repository mode remain available. No geometry or web implementation
changes. Existing web snapshot uses the resolved default automatically.

Added isolated catalog fixtures and tests for relocation, precedence, missing
roots, CLI recovery, discovery, candidate ambiguity, malformed manifests and
confinement. Updated README, operational guidance and durable specifications.

Commands performed: required `uv run cadcon info`, `generators`, `paths`; Ruff
fix/format on new code; full `uv run pytest -q --tb=short` and `uv run ruff check .`.
Initial sandbox runs hit Windows uv-cache and pytest-temp access restrictions;
validation reran successfully with reviewed access. No Git history operations.
