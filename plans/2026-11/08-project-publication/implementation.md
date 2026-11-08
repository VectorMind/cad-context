# Implementation

Progress: [x] implementation begun [x] publication CLI [x] project UI [x] migration [x] cold recovery [x] cleanup [x] validation.

Project registry output roots now move to portable-ID scoped workspace cache. Source and publication roots remain separate; no changes to project geometry definitions intended.

Delivered stable project identities, separate source/publication catalog bindings, verified rebuild/publish, checksummed source snapshots, non-overwriting restore, explicit dated release/freeze and source-conflict protection. Working model exports, measurement reports, historical comparison reconstructions and review sheets now use .cache/projects/animal-puzzle. The workbench root resolver also prefers the actual workbench over an unrelated model Git checkout.

The viewer now lists /projects and separates /projects/animal-puzzle (published consumers) from /projects/animal-puzzle/workbench (mutable local work). Legacy /project redirects to the listing. File access is allowlisted and realpath-confined; publication browsing does not depend on executing local generator code or retaining local cache.

Migrated durable model source to C:/dev/VectorMind/model-projects/animal-puzzle. The stable Drive project is projects/animal-puzzle; it contains web/latest, reference recovery/source bundles, and 3d-print/2026-10-25 only. Six previously delivered print files were preserved byte-for-byte; no new print release or freeze was created. Current web models are bear, elephant, rabbit and turtle, including the latest continuous-neck turtle. Source remains Git-ready and uncommitted; all Git history operations remain maintainer-owned.

Historical geometry-dependent tests were changed to regenerate comparison baselines from durable curves/settings/code. An old Fusion-specific elephant bevel is not reproduced exactly by the current kernel; source-outline comparisons and independent current-model proofs remain available. Exact historical bytes are not promised. Useful cache-only experiment source was preserved in the model source history before cleanup; disposable experiments and old test exports were removed after recovery validation.

Cleanup followed the explicit inventory recorded in shared reference/storage-migration.json and .cache/results/storage-migration.json. Dependency environments were retained. Windows script execution policy was left unchanged: native PowerShell commands were executed directly. Sandbox-owned disposable test directories required narrowly scoped DACL repair for the interactive account before removal, without following reparse points or deleting outside cache. Drive obsolete cad/exports/generated/history/source duplicates were removed only after archive checksum and rebuild proof.

Executed startup commands; project root/use; source snapshot/restore; full fresh export generation followed by --reuse-exports proof continuation; project publish; native project proof scripts; pytest/ruff; web check/test/build; durable verify-live.py; inventory-confined cleanup; and source-bundle refresh. See test.md for results and remaining review limits.

Follow-up, 2026-11-08: user explicitly requested keeping only the latest bear files within the legacy release. Verified all six original hashes, removed the two rejected r004 bear files, retained both r008 bear and both r010 elephant files unchanged, and updated release metadata/README. This explicit user-authorized historical cleanup is an exception to routine frozen-release immutability; it does not create or recommend a new release. Updated live inventory expectation and refreshed the shared workbench recovery bundle/validation inventory.
