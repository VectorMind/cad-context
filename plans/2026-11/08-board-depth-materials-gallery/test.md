# Validation

Startup cadcon info/generators/paths passed. New real GLB test covers separate parts, PBR factors, native volume and parent/global placement. Viewer tests cover preserved colour/roughness/metalness, default uncoloured surface and multi-material wireframe.

Full Python suite: 151 passed, 2 skipped; Ruff clean. Web check: zero diagnostics; 14 tests passed; production build passed with existing bundle-size advisory. Logs: .cache/reports/board-8mm-pytest.log and board-8mm-web.log.

Board verification passed 22/22; native volume 156944.289460633 mm3. Actual loaded assembly has nine valid solids, bounds 220 x 150 x 13 mm, zero tested inter-animal/board overlap; floor 3 mm, recess 5 mm. All project proof scripts passed via project rebuild --reuse-exports after checking unchanged animal source/artifact hashes. Actual GLTFLoader plus viewer material functions preserve all nine matte meshes and sketch palette within two sRGB levels. New release package hashes and ZIP CRCs pass; all eight animal packages equal the frozen approved release.

Live HTTP checks passed for all nine stages and 37 visuals, complete image links and checksums. Actual published GLB SHA256 matches the manifest, with nine meshes and five palette colours; current draft source relation is same-source. Gallery has nine comparison groups and nine single-image groups, preserving order. Receipts: .cache/results/board-8mm-live-page.json, project-visual-stages-live.json and board-8mm-viewer-colours.json. Browser screenshot inspection was unavailable; no screenshot verification is claimed. Physical printer fit remains untested.

Initial targeted pytest lacked explicit cache basetemp and was denied access to the old shared OS temp pytest root; reran under .cache/scratch. Initial export test used an unregistered generator with measurement enabled; changed the test to explicit measurement-free export and independent actual GLB geometry/material readback. No production check was relaxed.
