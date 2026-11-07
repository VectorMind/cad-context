Progress: ■■■ — quality profiles implemented and native CLI validation passed.

2026-11-07: Finer sampling independently passed the rounded-head 3MF package:
1,571,222 vertices / 3,142,440 faces; positive volume 21114.6610919 mm3;
all topology checks passed. Default head mesh remains unsuitable for printing.
Added typed Tessellation field to BuildResult, exporter propagation and sidecar
metadata. Separate print-quality external generator planned to limit preview cost.

Native documented CLI verify of the external fine print generator passed 18/18.
3MF profile is recorded in its project measurements; same B-rep STEP round-trip
passes. Ordinary preview remains a separate lighter generator. Download-only
project generators now route to project downloads instead of an unsupported viewer.
Validation: 118 pytest passed / 2 skips, Ruff clean, zero web type diagnostics,
11 web tests passed, production build passed (existing viewer bundle warning).
