# External Binaries As Declared Artifacts

Tools that are not Python packages (renderers, solvers, meshers) are declared,
fetched and resolved by the repository itself. They are never a manual install
step in a README, and never assumed to be on `PATH`.

## Declaration

`config/artifacts.yaml` declares every external tool: a description, a source,
a pinned version, a per-platform asset selector, an install directory under
`.tools/`, and the executable's path inside the unpacked asset.

Two source kinds are supported:

- `github-release` — an asset resolved from a pinned release tag through the
  GitHub releases API, selected by a glob pattern per platform.
- `url` — a direct download, for builds not published as GitHub release assets
  (nightly and snapshot channels).

Platform keys are `<sys.platform>-<arch>` (`win32-amd64`, `linux-amd64`,
`darwin-arm64`). An entry may declare a `sha256`; when present it is verified
before unpacking.

## Provisioning

`cadctx fetch <name>` (or `--all`) resolves the asset for the current platform,
downloads it into `.cache/downloads/`, verifies it, unpacks it into the declared
`install_dir` under `.tools/`, and reports the resolved executable path. A
fetch that finds the tool already installed reports `cached` and does nothing;
`--force` re-downloads and replaces. The download transcript goes to
`.cache/reports/`, not to the console.

`.tools/` is git-ignored: provisioned binaries are derived artifacts.

## Resolution At Runtime

A backend resolves its binary by checking `.tools/` first and `PATH` second, so
a fetched copy always wins over an ambient system install and runs are
reproducible.

## Absence Is Not Failure

A missing external binary degrades the affected path instead of breaking it:
the Python-side output is still produced (for a CSG backend, the source file),
the dependent formats are recorded as skipped with a reason, and the command
reports `degraded`. `cadctx info` shows which binaries resolved and which did
not. Test suites and CI stay green on a machine where no external binary has
been fetched.

## Adding A Tool

Adding an external tool means adding an entry to `config/artifacts.yaml` — not
new fetch code. The mechanism is generic across tools; anything that needs
bespoke provisioning logic is a sign the declaration schema should be extended
instead.
