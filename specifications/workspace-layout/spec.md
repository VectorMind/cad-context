# Workspace Layout And Output Discipline

Binding rules for where anything a run produces is allowed to land, and for how
much of it reaches the console.

## Single Output Root

Every execution — CLI command, test run, agent script, external-tool render —
writes below one git-ignored directory at the repository root:

```text
.cache/
  results/     # one small summary per command: <command>.json + <command>.md
  reports/     # long output that must not reach the console
  cad/         # generated geometry, at fixed per-generator paths
  scratch/     # throwaway scripts and experiments
  downloads/   # archives fetched for external binaries
.tools/        # unpacked external binaries
```

- Nothing under `.cache/` or `.tools/` is committed. Both are derived data.
- No generated file is written into `specifications/`, `plans/`, `src/`, or the
  repository root.
- The cache root is overridable with the `CAD_CONTEXT_CACHE` environment
  variable; the workspace root with `CAD_CONTEXT_ROOT`. Tests redirect the
  cache rather than writing into the developer's real one.
- The layout is machine-readable: `cadctx paths` prints it, and
  `cad_context.api.paths()` returns it. Consumers resolve paths from that
  contract instead of hardcoding directory names.

## Results: Small, Structured, One Per Command

Each command writes exactly two files, both overwritten on every run of that
command, so the directory has bounded size and stable paths:

- `.cache/results/<command>.json` — the full payload: status, timestamp, the
  facts shown on the console, the resolved file paths, and a `data` object with
  everything a caller might parse.
- `.cache/results/<command>.md` — the same content rendered for a human.
- `.cache/results/last.json` and `last.md` mirror the most recent command.

A result carries `status` from `ok`, `degraded`, `error`. A failure is still a
result: the command writes the result file, parks the traceback in
`.cache/reports/`, prints a one-line reason, and exits non-zero.

## Console: Quiet By Contract

The console is a status surface, not a log. A command prints:

1. one status line (`<status> <command> — <summary>`);
2. a small number of key facts, one per line;
3. the artifact paths it wrote (truncated with `(+N more)`);
4. the path of its result file.

Long output — subprocess logs, tracebacks, probe details, transcripts — goes to
`.cache/reports/<command>.log` and is referenced by path, never printed. No
progress spam, no scrolling walls of text. `--quiet` prints only the result-file
path; `--json` prints the result payload as JSON for programmatic callers.

## Geometry: Fixed Paths, Not Timestamped Ones

Generated geometry lives at a path derived only from the generator id and the
format:

```text
.cache/cad/<generator-id>/<generator-id>.<ext>
```

The path is stable across runs and across parameter changes. Regenerating
overwrites in place, so a browser tab, a viewer, or a web app can hold one URL
across an entire parameter-iteration session without re-resolving filenames.
Callers that deliberately want to keep several variants side by side pass an
explicit output directory; that is the exception, and it never becomes the
default.

## In-Memory Work Writes Nothing

The Python API (`cad_context.api`) is side-effect free: it builds geometry, it
returns data and live kernel objects, and it writes no files and no console
output. Producing files is an explicit, separate act — the `cadctx` CLI, or a
direct call into the export layer. A script that only needs numbers or a kernel
object leaves the workspace untouched.
