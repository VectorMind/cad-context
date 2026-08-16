# Agent And Human Interface

## CLI Surface

`cadctx` is the documented interface for every artifact-producing capability.
Commands are non-interactive, write structured result files, and are documented
in `README.md`. A capability without a documented command is not delivered.

Global discovery and selection options are `--json`, `--quiet`, `--project`,
and `--no-project`. Machine-readable discovery is:

- `cadctx info` — supported backend/tool availability and active project;
- `cadctx generators` — merged built-in/project registry and artifact roots;
- `cadctx schema <generator>` — parameter and exposure contract;
- `cadctx paths` — operational and per-generator output paths;
- `cadctx project info` — active project metadata without importing code.

Artifact commands are `generate`, `demo`, `verify`, and `fetch`. Project
lifecycle commands are `project init`, `project use`, `project clear`, and
`project info`. The preview server is started only through `cadctx web`.

## Python API

`cad_context.api` is the read-only/in-memory surface for exploration. It lists
the merged registry, returns schemas/defaults/status/paths, builds native
objects, and returns metrics. It writes no artifacts and exposes no additional
capability unavailable through the CLI. Scripts that explicitly need files call
the exchange layer or the CLI.

## Plain-File Routing

Repository routing lives in `README.md`, `AGENTS.md`, and `WORKFLOW.md`, not in
packaged agent skills or tool-specific manifests. Model-specific routing and web
exposure live in the external project's versioned `project.yaml`.
