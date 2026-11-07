# Validation

Fixtures: existing built-in plate2d and bracket-build123d generators, existing
Python suite/project fixtures, and installed web dependencies. Existing unrelated
working-tree changes were included in the checks.

Startup discovery under the pre-rename command passed using a repository-local
UV_CACHE_DIR after the default user cache was inaccessible. Info correctly
reported optional OpenSCAD unavailable.

Expected and actual results:

- `uv run cadcon --help`: installed usage is `cadcon`; passed after refreshing
  the editable installation with approved access to the existing user cache.
- `uv run --no-sync cadcon --json info`, `--quiet generators`, `--quiet paths`:
  structured discovery works; four built-ins listed, stable result paths returned.
- `uv run cadcon verify plate2d`: 7/7 checks passed.
- `uv run cadcon verify bracket-build123d`: 8/8 checks passed.
- `uv run --no-sync pytest -x --tb=short
  --basetemp=.cache/scratch/cli-rename-pytest`: 118 passed, 2 skipped.
  Log: `.cache/reports/cli-rename-pytest.log`.
- `uv run ruff check .`: all checks passed.
- `corepack pnpm check`: 27 files, zero errors/warnings/hints.
- `corepack pnpm test`: all 11 tests passed; symlink creation unavailable,
  lexical confinement tested.
- `corepack pnpm build`: passed; existing large viewer chunk warning remains.
  Check/build used `ASTRO_TELEMETRY_DISABLED=1` to avoid user-config writes.
- Direct web bridge imports with `node --experimental-transform-types
  --input-type=module`: default launcher returned four generators;
  `CADCON_COMMAND=.venv/Scripts/cadcon.exe` override returned paths successfully.
- Case-insensitive repository old-name scan excluding generated/dependency
  directories: no matches. `git diff --check`: passed.

Environment retries: local uv cache initially lacked hatchling and could not
access the network; the existing user cache resolved installation. Initial pytest
default temporary paths caused permission errors; rerunning under workspace cache
passed. Direct Node strip-only import needed TypeScript transformation enabled.
No remaining implementation gaps; optional OpenSCAD stays unavailable.
