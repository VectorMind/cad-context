# Upright SVG export

Scope: correct generic 2D SVG display orientation discovered while reviewing the
new external rabbit trace. CAD data is Y-up while SVG paint coordinates are Y-down.
This workbench change owns no model geometry or source data.

OP-001 resolved: flip the SVG path's display Y and its view-box origin together;
leave native coordinates, DXF and JSON unchanged. Confidence: high.

Exit: asymmetric translated geometry paints upright, remains in view, and its
horizontal orientation and margin are preserved. Existing verification passes.
