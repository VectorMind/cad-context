Progress: ■■■ — portfolio implementation and native checks complete; model parity remains separate and unresolved.

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

2026-11-02: Final checks: 112 pytest passed / 2 skips, Ruff clean, 11 web tests,
zero type diagnostics and successful production build. Historical F3D links are
explicit download-only entries, with no Fusion runtime. Existing HTML remains
unchanged. The page distinguishes historical statuses from current draft models.
Verified actual Chrome GLB/SVG/HTML rendering and corrected viewport height and
UTF-8 bridge output. Added JSON/PDF evidence links. Workbench sources remain in
the working tree; no git history operations.
