# Implementation

Progress: [x] diagnosis [x] display transform [x] regression [x] validation

Added a display-only Y reflection and adjusted the view-box top to -maxY-margin
in export2d.write_svg. The previous exporter wrote raw Y-up path data into a
Y-down SVG frame, so the asymmetric rabbit silhouette appeared upside down.
Added an asymmetric translated-triangle regression checking painted orientation,
horizontal preservation and framing. Durable exchange contract updated.

Rabbit source, evidence and generator remain external. Earlier unrelated working
tree changes were preserved. No second preview service or geometry code added.

Validated the final CLI rabbit SVG by rendering it with the installed webapp
sharp dependency and inspecting the upright ear/paw orientation. Regenerated
the external rabbit through cadcon verify (9/9). Full pytest: 129 passed,
2 skipped; Ruff clean. No further web implementation changed after its clean
check, 11 passing tests and successful build earlier in this task.
