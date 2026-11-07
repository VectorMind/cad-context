# Test record: native 3MF export

2026-11-01. Implementation and native Windows acceptance complete.

## Environment and execution

Windows CPython 3.12.14 (MSC v.1944, AMD64), native uv 0.12.7,
build123d 0.11.1, lib3mf 2.5.0. No dependency upgrades.
Native uv is C:\Users\wassi\.local\bin\uv.exe. Commands below use that
executable with Start-Process -Wait, captured stdout/stderr and checked ExitCode.
Logs and scratch scripts remain under .cache/reports and .cache/scratch.

Initial ordinary WSL uv startup failed on its read-only global cache. Retrying
with a writable uv cache replaced .venv with a Linux environment but could not
download dependencies. Moved that failed environment under .cache/scratch and
restored the Windows .venv through native `uv sync --locked --extra default`.
Native execution required elevated sandbox access for WSL interop. Actual
Windows uv output and exit codes were then established; Linux results are not
being used as acceptance evidence.

## Commands and results

| Command (native Windows) | Expected | Actual |
| --- | --- | --- |
| `uv sync --locked --extra default` | Restore locked Windows environment | Exit 0; installed locked build123d/lib3mf, unchanged dependency versions |
| `uv run --extra default cadcon --no-project info` | Fresh runtime/tool result | Exit 0; Python 3.12.14; Shapely/build123d/trimesh ready; degraded solely for optional OpenSCAD |
| `uv run --extra default cadcon --no-project generators` | Fresh registry | Exit 0; four built-ins with original format defaults |
| `uv run --extra default cadcon --no-project paths` | Fresh workspace paths | Exit 0; repository cache paths, no selected project |
| `uv run --extra default python .cache/scratch/mesher_smoke.py` | Confirm installed API, export and independently read asymmetric primitive | Exit 0; Windows platform and locked versions; one mesh/item, explicit mm, 8 vertices, 12 faces, volume 5083 mm³, bounds [0,0,0]–[13,17,23]; Mesher/lib3mf read one solid, Unit.MM |
| `uv run --extra default cadcon --no-project generate bracket-build123d -f 3mf` | Actual documented CLI 3MF artifact | Exit 0, status ok; stable .cache/cad/bracket-build123d/bracket-build123d.3mf |
| `uv run --extra default cadcon --no-project verify bracket-build123d -f 3mf` | Actual package and mesh proof | Exit 0, status ok, 16/16 checks; actual 3MF measurements, no STL dependency |
| `uv run --extra default cadcon --no-project verify plate2d` | Preserve SVG/DXF proof | Exit 0; 7/7 checks |
| `uv run --extra default cadcon --no-project verify airfoil` | Preserve SVG/DXF/JSON proof | Exit 0; 9/9 checks |
| `uv run --extra default cadcon --no-project verify bracket-build123d` | Preserve STEP/STL/GLB proof | Exit 0; 8/8 checks |
| `uv run --extra default cadcon --no-project verify wing-build123d` | Preserve loft STEP/STL/GLB proof | Exit 0; 8/8 checks; existing approximate-reference note |
| `uv run --extra default pytest` | Entire suite passes | Exit 0; final 103 passed, 1 skipped in 8.20 s |
| `uv run --extra default ruff check .` | No lint violations | Exit 0; All checks passed |
| `git diff --check` | No whitespace errors | Exit 0 |

Native logs: .cache/reports/native-sync.*, native-info.*, native-generators.*,
native-paths.*, mesher-smoke.*, info-final.*, generate-3mf.*, verify-3mf.*,
verify-plate.*, verify-airfoil.*, verify-bracket.*, verify-wing.*,
pytest-final.*, ruff-final.*. Files are operational evidence, not committed.

## Test fixtures and negative evidence

`tests/test_three_mf.py` adds 29 cases to the previous 74-test passing baseline.
All use redirected cache; project source is constructed entirely in tmp_path,
so no durable project fixture or real model output is modified.

- Asymmetric 13 × 17 × 23 mm native solid proves explicit units, signed volume,
  extents, vertices/faces, one mesh/item, and independent lib3mf re-import.
- A translated build instance proves its transform is applied exactly once;
  ZIP/XML measurements use trimesh with processing disabled and exact-coordinate
  welding for adjacency only, without automatic topology repair.
- Wrong units, extra mesh/build item, missing build/component references,
  duplicate resource IDs, bad vertex indices, nonfinite coordinates and bad
  transforms raise errors.
- Duplicate/degenerate faces, reversed single/all faces, open and disconnected
  meshes fail the relevant independent topology checks.
- Multiple solids and a solid with an extra wire reject explicitly.
- Atomic failure on a previous valid artifact leaves its bytes intact and no
  temporary artifact behind; invalid topology is rejected even with measure=False.
- A simulated malformed Mesher RuntimeError fails export rather than becoming
  an optional-runtime skip.
- Missing required 3MF and STEP yield verification error with failed presence
  checks. Simulated absent optional OpenSCAD rendering remains degraded, with
  available checks passing. The real optional SolidPython2 integration test is
  the single suite skip because that opt-in package is absent.
- Two generic external project generators each produce their own confined 3MF
  and measurements sidecar, with independently checked volumes; no bytecode is
  written to the project. Manifest format/backend validation rejects invalid
  combinations. No animal/model-specific core fixtures were added.
- Accompanying STL can be deleted and the actual 3MF still independently proves
  topology; existing STEP/STL/GLB and 2D tests pass.

Initial targeted tests loaded a CLI variable-shadowing bug detected by Ruff;
that run had 18 passes and one failure. Corrected the bug, then obtained 96
passes/1 skip. Final added single-solid/degradation regressions yielded the
103 passes/1 skip above. These supersede the initial failing run.

## Gaps and scope

No unresolved implementation or required acceptance gaps. No web sources
changed: its generic confined artifact route serves unknown extensions as
application/octet-stream and already supports 3MF downloads. Conditional web
checks/tests/build were therefore not required. Slicer profiles, assemblies,
and slicer automation are outside this geometry-only single-piece scope.
No history-changing git command was run; finished work remains in the tree.
