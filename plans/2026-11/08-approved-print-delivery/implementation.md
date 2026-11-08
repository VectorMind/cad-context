# Implementation

Progress: [x] read-only failure reproduced [x] confined cleanup retry [x] regression test [x] native geometry/approval comparison [x] shared release and recovery validation.

The initial project publish swapped the approved web/latest successfully, then failed removing web/.latest-previous because Windows Drive marked that directory read-only. The old files had already been removed; only hidden desktop metadata and the protected directory remained. Verified the exact literal path, refused a reparse point, cleared its read-only bit and removed that obsolete staging tree. No current model was deleted.

publication._remove_publication_tree now validates the tree's parent boundary and retries only PermissionError targets within that tree after chmod. Publish/release cleanup paths use it. The regression publishes twice with the first latest directory chmod 0555, then asserts current files and absence of old staging. No geometry/export algorithm changed.

The separately authorized model delivery regenerates/verifies all declared artifacts, compares all 13 native models and four actual viewer meshes with their approved baselines, publishes matching metadata and freezes the eight-piece release dated 2026-11-08. Source recovery bundles include final approval and provenance records. See the external model packet plans/2026-11/08-approved-print-release/ and shared release validation JSON.

Actual Drive republish passed with the read-only cleanup fix. CLI release --freeze and independent freeze checksum check passed; eight delivered ZIP packages passed CRC and exact hash/provenance checks. Consumer indexes identify 2026-11-08 as the current approved delivery; 2026-10-25 remains clearly superseded. Model and workbench recovery snapshots refreshed after final documentation.
