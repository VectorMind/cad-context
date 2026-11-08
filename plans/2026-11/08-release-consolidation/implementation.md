# Implementation

Progress: [x] inspected three release folders [x] policy clarified [x] merged and verified [x] recovery refreshed.

Consolidation uses the latest 8 mm manifest as the geometry authority, preserves unknown/user files, checks destination hashes before removing only the two explicitly named source folders, and records hashes of all user G-code. Existing G-code is not revalidated for the revised board.

The destination now contains nine generated 3MFs and nine user G-code files. All hashes verified before removal of the two duplicate folders. Drive read-only directory attributes initially prevented deletion; cleared attributes only within the two checked paths and completed cleanup. Manifest uses the current source identity and retains draft status for the board; it does not claim a new physical-fit approval. Historical manifests are preserved as metadata in reference/release-consolidation.json.
