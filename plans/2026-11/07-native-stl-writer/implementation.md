# Implementation

Progress: [x] native writer probe [x] explicit selection [x] regression [x] validation

Added a validated STL writer selection to Tessellation and routed the opt-in
through build123d Mesher with millimetre units and existing deflections. Kept
default serialized profiles unchanged. Added a real STL/GLB regression proving
the selected native writer is used, outputs are watertight and volume agrees.

The standard writer retained degenerate triangles in both rabbit pieces even
after tessellation/ASCII probes; native Mesher already used for 3MF produced
watertight STL/GLB at the same quality. No post-export mesh repair was added.

Added explicit unavailable-runtime reporting for STL and derived GLB. Final full
pytest: 132 passed, 2 skipped; Ruff clean. Rabbit front/rear verify 22/22 each,
display assembly 7/7, with native geometry and independent volume references
unchanged. Web check clean, 11 web tests passed and build passed (existing bundle
warning). Default export selection and serialized quality payload remain intact.
