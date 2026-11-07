# Validation

- Required startup: info/generators/paths passed, animal puzzle active; optional
  OpenSCAD unavailable as before.
- `uv run pytest -o addopts= -q --tb=short`: 128 passed, 2 skips in 10.98 seconds.
  New fixture proves characters-generation, ordinary folders, malformed manifests
  and invalid marked projects are excluded; registered legacy projects still work.
- `uv run ruff check .`: all checks passed. External source snapshots also clean
  after import sorting only.
- `cadcon --project airfoil-wing verify airfoil-wing-profile`: 9/9.
- `cadcon --project airfoil-wing verify airfoil-wing-loft`: 8/8.
- `cadcon --project reference-parts verify reference-plate`: 7/7.
- `cadcon --project reference-parts verify reference-bracket`: 22/22, including 3MF.
- Original cache artifacts: all 12 SHA-256 values matched preserved Drive copies
  immediately after copying and again after verification, before deleting originals.
  Source file paths were confined to the four named .cache/cad directories; only
  checked files were removed, followed by non-recursive removal of empty folders.
- Native `cadcon project list`: exactly animal-puzzle (default), airfoil-wing and
  reference-parts, all available. characters-generation remains untouched and absent.
- Native `cadcon project info`: default animal puzzle still at its original shared
  Drive path. Local models binding points to ~/My Drive/Projects/3d-models.

Operational proof: `.cache/reports/drive-project-migration-proof.json` and original
inventory `.cache/reports/cache-migration.json`. Durable model-specific test packets,
verification JSON, source inventories and cache-copy hashes are in each external
project's plans/ and evidence/ folders. Original full parameter provenance was
unavailable; exact original bytes are retained separately from fresh defaults.

No web implementation changed. No remote synchronization, physical manufacturing,
or aerodynamic performance validation is claimed.
