# Implementation: Default Library And Project Folder Workflow

## Progress

`▰▰▰▰▰▰ Done` — all six phases implemented and proven on 2026-08-16.

## Implemented Changes

- Added versioned external project manifests, precedence (`--project` > env >
  persisted pointer), `--no-project`, and `project init/use/clear/info`.
- Resolved the project-independence promise to the supported
  build123d/Shapely/OpenSCAD toolchain; arbitrary project environments remain
  outside scope.
- Added strict safe-YAML validation, lazy collision-proof module namespaces,
  trusted-code disclosure, no project bytecode writes, slug validation, and
  hard-stop generator collisions.
- Routed project artifacts and stable measurement summaries to project `cad/`
  while keeping operational results under the repository cache. Export writes
  now use same-directory temporary files followed by replacement.
- Replaced cross-backend `compare` with format-aware `verify` for 2D and 3D.
  STEP re-import now uses build123d instead of CadQuery.
- Removed the CadQuery backend, dependency/pin workaround, built-in CadQuery
  generators, built-in OpenSCAD bracket variant, and variant exposure entries.
- Kept OpenSCAD as an optional project toolchain and added a copied temporary
  project fixture that proves SCAD emission and missing-binary degradation.
- Made registry/schema payloads carry origin, project, exposure, and artifact
  root. The web process snapshots one project at startup, groups project models,
  and confines served real paths to each generator root.
- Replaced the durable backend, project, workspace, exchange, agent-interface,
  and web contracts and rewrote the README/AGENTS routing for the focused core.

## Review-Time Decisions

- `cadctx verify` is the accepted command name.
- Verification is format-aware rather than 3D-only.
- A running web server never live-switches projects; restart is the explicit
  behavior.
- `project init` precedes `project use`; `--dry-run` is the non-writing real
  evidence-folder validation path.
- The speculative OneDrive staging copy was deferred because it would not solve
  output locking without a copy-back protocol and no import lock was observed.

## Final Proof

- `uv run ruff check .` — all checks passed.
- `uv run pytest` — 75 passed.
- `corepack pnpm check` — 23 files, zero errors/warnings/hints.
- `corepack pnpm test` — 10 passed; `corepack pnpm build` completed.
- All four built-ins passed `cadctx verify`; a copied external project passed
  discovery, generation, verification, and live web artifact serving.
- `project init --dry-run` validated the real cache-barriere folder without
  changing it.
- Full commands, measurements, and observed results are recorded in
  [test.md](./test.md).
