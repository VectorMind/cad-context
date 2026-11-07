# Validation

Startup commands passed before work. Native Windows environment, local uv cache.
Real external rabbit Mesher STL/GLB probes watertight for both pieces; volume
agreement within 1%.

- `uv run pytest --basetemp=.cache/scratch/native-stl-writer-pytest`: 132 passed,
  2 skipped. Includes real Mesher STL/GLB readback, native-volume preservation,
  rejection of unknown writer and explicit missing-runtime skips.
- `uv run ruff check .`: passed after formatting one exception line.
- `cadcon verify animal-puzzle-rabbit-rounded-front/rear`: 22/22 each.
- `cadcon verify animal-puzzle-rabbit-rounded-review`: 7/7.
- Project proof: every identified corner, circular carriers, full top/bottom rims,
  mouth outlets/floors and clean-process repeatability passed.
- Web check zero diagnostics, 11 tests passed, build passed with existing
  Three.js chunk warning. No web source changes required.

Standard OCCT/ASCII/tessellation probes retained degenerate STL facets on this
fine-feature fixture. Native Mesher handles its own vertex indexing as in 3MF;
no post-export triangle cleanup or tolerance relaxation was introduced.
