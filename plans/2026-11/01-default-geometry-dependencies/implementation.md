Progress: [■■■] Dependencies, documentation, lockfile, and validation complete.

Promoted build123d, drawsvg, ezdxf, manifold3d, Shapely, and trimesh to required
dependencies. Kept former extra names as empty compatibility aliases; `all`
still selects optional OpenSCAD. Updated README and backend policy together.

Startup checks reproduced the issue: an installation without extras reported
zero available geometry backends. Validation uses an isolated environment at
`.cache/scratch/validation-venv` to avoid replacing the shared Windows `.venv`.

Ran plain `uv sync` with only `UV_PROJECT_ENVIRONMENT` redirected. It installed
the geometry stack and refreshed `uv.lock` without upgrading package versions.
Ran `uv run cadcon --no-project verify plate2d`, `uv run pytest`, and
`uv run ruff check .` successfully. A locked offline dry run with the legacy
`default` extra required no changes. `cadcon info` now reports Shapely,
build123d, and trimesh available; optional OpenSCAD remains absent.

No web source changed, so web checks were not required. Windows execution was
not available; validation ran on Linux with the cross-platform uv lockfile.
