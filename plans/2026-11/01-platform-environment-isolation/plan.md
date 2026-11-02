# Platform Environment Isolation

Approved scope: prevent agents running under Linux/WSL from replacing the
Windows `.venv` in a shared checkout. The user requested a workflow correction
after Windows `uv sync` could not remove a Linux-created `lib64` symlink.

Milestones: place environment selection before startup commands in AGENTS.md;
document the durable contract and user-facing WSL setup; validate startup
commands through an existing isolated Linux environment.

Dependencies: uv's existing `UV_PROJECT_ENVIRONMENT` support. Risk: shell
variables must be supplied in every agent shell invocation and inherited by
child processes. Exit criteria: workflow explicitly reserves `.venv` for
Windows and isolated Linux commands work. Open points: none.
