# Handoff: continue the animal puzzle in cad-context

Updated 2026-11-01. This file carries the conversation context into a fresh
session. The generic 3MF workbench packet is complete. The next task is the
external animal-puzzle migration, beginning with the accepted bear.

## User intent and settled choices

- Leave Fusion 360 completely, including its MCP workflow. Recreate editable
  shapes, primitives and construction operations in build123d. Historical STEP
  files are comparison references, not substitutes for editable reconstruction.
- Prefer native Windows PowerShell, uv and Python. Keep Windows paths in
  commands and user-facing instructions. Do not switch the modelling workflow
  to WSL to work around a launcher problem.
- Keep model sources and evidence in the existing shared Drive project, outside
  the workbench repository. No copying the animal project into core source.
- Preserve reviewed curves, canonical seams, engraving endpoints and existing
  releases. Compare reconstructed geometry and appearance before continuing
  design work. Do not retrace accepted artwork unnecessarily.
- Use build123d Mesher/lib3mf through cadcon for generic geometry-only 3MF,
  one physical piece per file. No new CAD backend or slicer automation.
- Resolve routine technical choices autonomously. Ask only for an actual design
  decision or a demonstrated discrepancy requiring a change to accepted shape.
- The maintainer owns git operations. Preserve working-tree changes; do not
  stage, commit, push or reset them.

## Completed workbench dependency

Read [implementation.md](implementation.md), [test.md](test.md), and
[plan.md](plan.md). They record native Windows acceptance; those tests were not
rerun merely to write this handoff.

- 3MF export, independent package/mesh measurements, atomic validation and
  single-solid restrictions are implemented.
- Both generate and verify accept repeated `--format/-f`; declared project
  formats can include `3mf`. Missing required artifacts fail verification.
- A fresh Mesher can contain an unused component resource: the contract permits
  it with valid references while requiring one printable mesh and one direct
  build item. Do not incorrectly reject all additional resource types.
- Native Windows proof: 103 pytest passes, one optional OpenSCAD skip, Ruff
  clean, real CLI 3MF verification 16/16. Four built-in default verifications
  also passed. No web changes or dependency upgrades were needed.
- Versions proved: Windows Python 3.12.14, uv 0.12.7, build123d 0.11.1,
  lib3mf 2.5.0. Optional OpenSCAD absence is not a migration blocker.
- Current contracts are in `specifications/3mf-export/spec.md`,
  `specifications/exchange-formats/spec.md` and
  `specifications/model-projects/spec.md`; README documents CLI usage.

Do not reimplement the exporter or reopen the exporter choice. Revalidate only
as required by new changes or a changed runtime.

## Locations and reading order

Workbench:

```text
C:\dev\vectormind\cad-context
```

External project:

```text
C:\Users\wassi\My Drive\Flatshare\3D Models Shared\projects\2026-10-24-animal-puzzle
```

Within that external project read:

1. `HANDOFF-CADCON.md`
2. `specifications/cadcon-migration/spec.md`
3. `plans/2026-11/01-cadcon-handoff/plan.md` and `test.md`
4. Current `handoff.md`, `parameters.json`, `spec.md`,
   `spec/visual-fidelity.md` and `spec/lessons-learned.md`
5. Shared parent `AGENTS.md` and `workflow.md`, interpreted with the user's
   explicit instruction to stop using Fusion for this project.

The external migration documents predate the completed 3MF implementation.
Their statements that native runtime proof and the exporter are pending are
now stale; this packet supplies the completed evidence. Update those statuses
when starting the migration, preserving the original planning history.

At this handoff inspection, the external `project.yaml` is absent. No model
migration completion is claimed. Inspect again before initialization because
another session or Drive sync may have changed the folder.

## Immediate next work

1. Read the current repository AGENTS.md and prove the native runtime with
   cadcon info/generators/paths. Use `--extra default` with uv run to retain
   installed geometry extras. Do not recreate the Windows environment.
2. Reconcile the external migration packet with the now-complete 3MF dependency.
   Create its implementation.md when model implementation begins, following
   the required Progress line and evidence conventions.
3. Inventory baseline inputs/exports and record their hashes as evidence.
   Check current metadata before replacing existing documents. Add a scoped
   project workflow override so other shared projects retain their policies.
4. Run `cadcon project init <path> --dry-run`, inspect the scaffold, then init
   if the manifest is still absent. Use global `--project <path>` during initial
   validation. Selecting the project later trusts its Python generator code.
5. Recreate the bear from `inputs/bear-r007-beziers.json`,
   `parameters.json/cad_r008`, and the construction sequence in
   `src/build_bear_r008.py`. Register front/rear generators with shared helpers;
   builders return BuildResult and never write files.
6. Rebuild twice in clean processes. Compare with
   `exports/bear-r008-review.step` and r008 evidence: exact source curves,
   placement, bounds, volumes, seams, named landmarks and actual top-view
   overlays. Preserve independent analytic or explicitly approximate references.
7. Generate and verify STEP/STL/GLB/3MF through cadcon. Outputs belong at stable
   `cad/<generator>/` paths with measurement sidecars. Verify the actual 3MF,
   not merely an accompanying STL. Update project test evidence and portfolio.
8. Once bear parity is established, repeat for the elephant using
   `inputs/elephant-r009-beziers.json`, `parameters.json/cad_r010`,
   `src/build_elephant_r010.py`, and `exports/elephant-r010-review.step`.
   Preserve the shared source scale. Do not reuse the Fusion-specific triangle
   repair script automatically.

Bear r008 appearance is accepted; r004 is rejected. Elephant r010 is built
and historically checked but still awaits visual acceptance. The proposed
piece generator IDs are animal-puzzle-bear-front, animal-puzzle-bear-rear,
animal-puzzle-elephant-front and animal-puzzle-elephant-rear. Review assemblies
may use STEP/GLB but must not become combined print releases.

## Native execution and environment protection

Native uv is `C:\Users\wassi\.local\bin\uv.exe`. The completed packet found
that ordinary child invocation through the session launcher could yield no
output or usable exit code. Native PowerShell `Start-Process -Wait -PassThru`
with redirected stdout/stderr and explicit ExitCode solved this. A reusable
operational helper currently exists at `.cache/scratch/native.ps1`; inspect it
before use, and recreate it if absent because cache files are not durable.

Example native PowerShell invocation pattern, from the workbench directory:

```powershell
New-Item -ItemType Directory -Force '.cache\reports' | Out-Null
$process = Start-Process -FilePath 'C:\Users\wassi\.local\bin\uv.exe' `
  -ArgumentList 'run --extra default cadcon --no-project info' `
  -Wait -PassThru -NoNewWindow `
  -RedirectStandardOutput '.cache\reports\handoff-info.out' `
  -RedirectStandardError '.cache\reports\handoff-info.err'
Get-Content '.cache\reports\handoff-info.out'
Get-Content '.cache\reports\handoff-info.err'
if ($process.ExitCode -ne 0) { throw "cadcon exited $($process.ExitCode)" }
```

Quote the full external project path when constructing process arguments; it
contains spaces. Require fresh result artifacts and actual exit codes.

Earlier Linux uv attempts replaced the shared Windows .venv; it has since been
restored and native acceptance passed. Never repeat that recovery mistake.
The latest AGENTS.md requires Linux/WSL uv, if independently needed, to set
`UV_PROJECT_ENVIRONMENT="$PWD/.cache/scratch/venv-linux"` in every invocation,
including tests and child processes. Never use Linux uv against shared .venv,
never use uv --active to select Windows from Linux, and never persist a Linux
override in shared pyproject.toml. Such isolated checks do not replace this
project's native Windows acceptance requirement.

## Decisions that remain outside the migration

No user decision is needed to begin faithful reconstruction. Reproduction
dimensions remain provisional. Final board dimensions, fit clearances,
printer/material settings, rabbit/turtle geometry, shared nesting and physical
testing are subsequent design work. Elephant visual approval is still pending.
Do not turn the roughly 215 x 156 mm image-derived board estimate into an
approved dimension. If parity requires changing accepted bear appearance,
present the specific discrepancy and alternatives before making that change.

Local file readback is not proof of remote Google Drive synchronization.
Keep those claims separate. Use only cadcon web for the preview server and
restart it after switching projects.

## Suggested first message in the fresh conversation

> Read plans/2026-11/01-native-3mf-export/handoff.md. The generic 3MF feature is
> complete. Implement the external animal-puzzle migration plan on native
> Windows, starting with faithful reconstruction and verification of the
> accepted bear, then the elephant. Keep Fusion out of the runtime, preserve
> historical files, and ask me only when an actual design decision is needed.
