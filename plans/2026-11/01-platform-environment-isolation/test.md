# Validation

Fixture: shared checkout with Windows `.venv` and a separate existing Linux
environment at `.cache/scratch/validation-venv`.

Commands used prefix `UV_CACHE_DIR=/tmp/cadcon-uv-cache
UV_PROJECT_ENVIRONMENT=.cache/scratch/validation-venv` (as two shell variable
assignments) to avoid the sandbox's read-only default uv cache and protect
Windows `.venv`.

| Command | Expected | Actual |
| --- | --- | --- |
| `uv run --no-sync cadcon info` | Linux CLI works in isolation | Passed; maintained backends ready, optional OpenSCAD absent |
| `uv run --no-sync cadcon generators` | Built-ins discoverable | Passed; four ready |
| `uv run --no-sync cadcon paths` | Resolve repository layout | Passed |
| `git diff --check` | No whitespace errors | Passed |

Reviewed AGENTS.md ordering: the environment rule precedes all startup uv
commands and explicitly covers fresh shell invocations and child processes.
No runtime code changed; pytest and web builds were not needed for this
documentation-only workflow correction. This is an agent instruction, not a
technical interception of arbitrary manual uv commands.
