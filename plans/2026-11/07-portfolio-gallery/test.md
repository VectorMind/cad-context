# Validation

Follow-up removal validation: required startup commands passed; web check clean,
11 web tests passed, build passed with existing bundle-size warning. Pytest with
`--basetemp=.cache/scratch/portfolio-removal-pytest`: 128 passed, 2 skipped;
Ruff clean. Live `/project` returned 200 with all nine gallery images, models
and drawings, and no iframe, portfolio anchor or earlier-portfolio section.
External archive files were preserved. Prior screenshot-host limitation remains.

Required startup commands: info, generators, paths passed using repository-local
UV_CACHE_DIR after the system uv cache denied access. Active animal project and
eight registry entries confirmed. Optional OpenSCAD absent.

Results:

- `corepack pnpm test`: 11 passed; symlink creation unavailable on Windows,
  lexical confinement checks passed.
- `ASTRO_TELEMETRY_DISABLED=1 corepack pnpm check`: 27 files, no diagnostics.
- `ASTRO_TELEMETRY_DISABLED=1 corepack pnpm build`: passed; existing large
  Three.js bundle warning remains.
- `uv run pytest --basetemp=.cache/scratch/portfolio-pytest`: 128 passed,
  2 skipped. Initial default temp path was inaccessible; local basetemp resolved it.
- `uv run ruff check .`: passed.
- `uv run python .cache/scratch/portfolio-restore/verify.py`: live viewer and
  portfolio image routes return 200, nine images in each; original embedded
  portfolio returns 200. Summary: `.cache/results/portfolio-gallery.json`.

No geometry changed, so no generator rebuild/measurement was needed. Native
computer-use pipe and browser host are unavailable; screenshot and viewport
inspection could not be completed. Responsive card constraints were verified
in the served CSS, but appearance at device sizes remains uninspected.
