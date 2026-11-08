# Board depth, authored materials and compact gallery

User selected 8 mm board (3 mm floor + 5 mm recess), solid sketch colours in the loaded nested-board preview, and smaller two/three-column project photos. Model implementation/specs/geometry proof belong in the external animal project. Workbench scope: preserve native assembly colours in GLB export and authored PBR materials in the viewer, and compact staged image layout without losing order/full-size links.

GLB colour export is opt-in via native per-part colours; uncoloured exporters and printer packages retain existing behavior. Preserve global assembly placement, material colours, opaque matte PBR appearance and existing millimetre/Z-up convention. No new geometry backend or frontend geometry implementation. Gallery groups adjacent single images into three columns and internally multi-panel sheets into two, reducing on narrow screens.

Exit: real colored GLB readback preserves distinct parts/colours and bounds; viewer material/wireframe tests pass; old uncoloured display stays the same; full Python/web checks; live model and image readback; new dated board candidate and matching sources, with old animal packages byte-identical. Git remains maintainer-owned.
