Progress: ■□□ — implementation begun.

2026-11-01: Inspected CLI project metadata, manifest, existing artifact route and
ModelView. Native startup passed. Chosen explicit portfolio allowlist to preserve
external ownership and avoid exposing arbitrary project files.

Added manifest metadata, confined portfolio route, sandboxed HTML/SVG responses,
project page with interactive models and declared images, and homepage link.
Type check and 11 web tests passed; production build passed (existing large
3D-viewer chunk warning). Corepack's default pnpm 12 launcher was missing;
explicit pnpm 10.20.0 worked without changing the dependency lock.

Real curved model export exposed a generic bounds bug: coordinate-relative mesh
tolerance rejected a tessellated extremum near zero. Added a shared extent-based
absolute budget capped by tessellation deflection, with translation-invariance
regression. This leaves historical parity and STEP tolerances unchanged.
