# Local builds and explicit project publication

Approved: all working geometry/tests/reviews in local cache; durable source outside cache; Drive holds latest renderer assets, useful reference/continuation source and user-controlled dated print releases. No generated historical model archives except delivered print releases. Explicit project listing/URLs replace ambiguous /project navigation.

Milestones: local project cache isolation; consumer publication/restore/rebuild CLI; /projects and /projects/<id> with published/local distinction; migrate animal source and baseline dependencies; validate empty-cache rebuild; inventory-based cleanup only after recoverability proof; tests and durable contracts.

OP-001 resolved: durable local source C:/dev/VectorMind/model-projects/animal-puzzle, portable source snapshot on Drive for continuation while maintainer owns Git commits. OP-002 resolved: no new print release automatically; retain existing delivered packages under original date. OP-003 resolved: discard regenerated geometry history, retain sources/references and prior acceptance records; migrate mesh-dependent checks to reconstruction.

Exit: cache-loss recovery rebuilds current models without Drive work exports; renderer reads published GLBs independent of cache; explicit freeze prevents release overwrite; cleanup verified by final inventory. No Git history operations.
