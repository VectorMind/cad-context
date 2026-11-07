# Validation

Startup cadcon info/generators/paths passed before implementation. Native Windows
environment with local UV_CACHE_DIR.

- `uv run pytest --basetemp=.cache/scratch/svg-y-up-pytest`: 129 passed,
  2 skipped; includes the asymmetric translated-triangle orientation regression.
- `uv run ruff check .`: passed.
- `uv run cadcon verify animal-puzzle-rabbit-trace`: 9/9 passed after correction.
- Rasterized final CLI SVG through installed sharp and visually inspected upright
  ears/paws at `.cache/scratch/rabbit-cli-upright.png`.
- Web check: zero diagnostics; web tests: 11 passed; build passed with existing
  Three.js chunk warning earlier in this task. Web sources unchanged by this fix.

DXF/JSON coordinates and native Shapely geometry are unchanged. No browser
screenshot available in this session; artifact raster inspection was completed.
