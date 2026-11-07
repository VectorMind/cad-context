# Generator-owned tessellation quality

User scope: finish the rounded bear and make its exports reviewable. A measured
head/rim case fails at default tessellation but succeeds at finer sampling,
without changing geometry. Deliver a generic export quality field, with all
model settings remaining external.

Milestones: typed positive finite quality settings; STL/GLB/3MF propagation and
measurement metadata; documented project-generator example; regressions and
native CLI proof. Defaults remain 0.01 / 0.1. No topology repair or new backend.

OP-001 resolved: BuildResult.tessellation is generator-owned; separate external
print generator keeps large meshes out of ordinary previews. Confidence high.
Risk: large files and long validation. Exit: default behavior retained, explicit
fine profile independently verified, quality recorded in measurements.
