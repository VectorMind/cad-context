# Validation

Fixture: repository built-ins, no active project; isolated Linux validation
environment at `.cache/scratch/validation-venv` via `UV_PROJECT_ENVIRONMENT`.

Before the change, `uv run cadcon info` reported 0/4 backends available;
`cadcon generators` listed all four built-ins as unavailable. Startup commands
`info`, `generators`, and `paths` completed. Initial sandbox attempts failed
because the default uv cache was read-only; downloads required network access.

All commands below used `UV_PROJECT_ENVIRONMENT=.cache/scratch/validation-venv`.
Sandboxed commands also used `UV_CACHE_DIR=/tmp/cadcon-uv-cache` because the
default cache is read-only. Installation ran with network access.

| Command | Expected | Actual |
| --- | --- | --- |
| `uv sync` | Install maintained geometry without extras; refresh lock | Passed; installed Shapely, build123d, trimesh, manifold3d, ezdxf, drawsvg and their dependencies; existing package versions retained |
| `uv run cadcon info` | Maintained backends available; OpenSCAD optional | Shapely, build123d, trimesh available; OpenSCAD absent (`degraded` as expected) |
| `uv run cadcon --no-project verify plate2d` | Valid SVG/DXF and analytic agreement | 5/5 checks passed; native area 8296.4044 versus approximate reference 8296.3451, within 1% |
| `uv run pytest` | Suite passes | 74 passed, 1 skipped in 46.37 seconds |
| `uv run ruff check .` | No lint findings | All checks passed |
| `uv sync --locked --offline --extra default --dry-run` | Legacy extra accepted; lock consistent | Audited 66 packages; would make no changes |
| `git diff --check` | No whitespace errors | Passed |

Pytest log: `.cache/reports/default-dependencies-pytest.log`.
Plate proof: `.cache/results/verify-plate2d.json`.
The ezdxf home-cache warning did not affect export or verification.

Gaps: Windows installation was not executed; Linux validated the dependency
contract using the universal lockfile. Web source and geometry code did not
change, so no web rebuild or additional geometry tests were needed.
