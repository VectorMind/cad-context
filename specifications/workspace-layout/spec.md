# Workspace Layout And Output Discipline

## Operational Cache

Every operational result remains below the repository's git-ignored cache:

```text
.cache/
  results/     # one small JSON/Markdown result per command
  reports/     # long subprocess logs and tracebacks
  cad/         # built-in generator artifacts
  scratch/     # throwaway scripts and experiments
  downloads/   # fetched archives
  active-project.json
.tools/        # unpacked external binaries
```

The cache root is overridable with `CAD_CONTEXT_CACHE`; the repository root with
`CAD_CONTEXT_ROOT`. Tests redirect the cache. Nothing under `.cache/` or
`.tools/` is committed.

An active external project adds a durable geometry root while leaving
operational noise in the repository cache:

```text
<project>/cad/<generator-id>/<generator-id>.<ext>
<project>/cad/<generator-id>/<generator-id>.measurements.json
```

Built-in generators continue to write under `.cache/cad/`, even while a project
is active. Consumers resolve per-generator artifact roots from `cadctx
generators` or `cadctx paths`; they never infer one global root.

## Results: Small, Structured, One Per Command

Each command writes `.cache/results/<command>.json` and `.md`, overwriting the
same stable names. `last.json` and `last.md` mirror the most recent command. A
result has status `ok`, `degraded`, or `error`; failures still write a result and
park their traceback in `.cache/reports/`.

The console is a status surface: one status line, a few facts, a few paths, and
the result path. Long output belongs in reports. `--quiet` prints only the result
path and `--json` prints the result payload.

## Fixed And Atomic Geometry Paths

Artifact paths derive only from generator id and format and are overwritten in
place. A viewer URL therefore stays stable through a parameter-iteration
session. Writers create a same-directory temporary file and replace the target
when complete. `--out-dir` is the explicit exception for callers keeping
several variants side by side.

Generator ids are validated slugs, and web routes confine resolved real paths to
the registry-provided artifact root.

## In-Memory Work Writes Nothing

The Python API returns data and live native objects without writing files or
printing. Project code executes only when its schema or build is requested and
is bound by the same no-write builder contract. Artifacts require the CLI or an
explicit call to `cad_context.exchange.export`.
