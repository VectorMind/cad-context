# Implementation

Progress: [x] identified material flattening [x] native-part GLB path [x] viewer material preservation [x] compact image groups [x] validation [x] publication/recovery.

Added optional coloured native leaf tessellation at the exporter boundary, including inherited colour and global assembly location. Each part exports separately into a named GLB mesh with matte opaque PBR material; native sRGB palette converts to linear glTF base factors. The uncoloured STL-to-GLB path remains the default. Actual native geometry stays inside generators/exporters.

Viewer now preserves explicitly authored GLB materials instead of replacing them with grey. It still applies lit flat shading for missing normals and the default CAD surface for files without authored materials. Wireframe supports material arrays without changing colours. Compact gallery preserves image order by grouping adjacent single images into three-column rows and comparison sheets into two-column rows; no more full-row wide sheets, with full-size links retained.

Published the revised 220 x 150 x 8 mm board (3 mm floor, 5 mm recess), coloured loaded preview, and compact gallery. New draft 2026-11-08-nested-board-8mm contains the board plus eight byte-identical approved animal packages. Prior 9 mm draft is explicitly superseded. Model source and workbench recovery archives are refreshed after final documentation. No server restart or Git history operation.
