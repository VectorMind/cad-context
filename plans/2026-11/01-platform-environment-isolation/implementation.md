Progress: [■■■] Workflow, durable contract, documentation, and checks complete.

Cause: the earlier agent's Linux `uv run` startup check recreated a shared
Windows `.venv`, leaving a Linux `lib64` symlink that Windows uv could not
remove. This was an environment-selection mistake, not a need to change the
default geometry dependencies.

AGENTS.md now requires a separate Linux environment before every uv command,
including startup checks, sync, tests, lint, and web launch. It prohibits
Linux operations on shared `.venv` and keeps the override in the calling shell.
Updated workspace-layout spec and README in the same pass.

Reused `.cache/scratch/validation-venv` for read-only startup verification with
`UV_PROJECT_ENVIRONMENT` set explicitly. No Windows environment was modified.
No application code changed.
