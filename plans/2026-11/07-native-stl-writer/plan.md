# Explicit native Mesher STL export

Scope: allow project generators to select build123d Mesher for STL and derived
GLB when the standard OCCT writer retains degenerate triangles at small fillets.
Discovered during the approved external rabbit build; model code stays external.

OP-001 resolved: opt-in Tessellation.stl_writer='mesher'; retain 'occt' default
and the existing default serialized profile. Confidence: high; real rabbit
Mesher STL/GLB probes are watertight and within 1% of native/reference volume.

No new backend, binary or dependency, no manual triangle repair. Exit: real
STL/GLB readback, unchanged native solid, passing tests/Ruff and model CLI proof.
