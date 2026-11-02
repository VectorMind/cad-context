# Default Geometry Dependencies

Approved scope: make plain `uv sync` sufficient for the maintained CLI and web
geometry stack, as requested by the user after a missing-Shapely preview error.

Milestones: promote maintained geometry dependencies, retain old extra names,
refresh the lockfile, update installation documentation and backend policy,
then validate plain installation, plate verification, pytest, and Ruff.

Dependencies: existing locked packages and package-index access for validation.
Risk: the standard installation is larger; OpenSCAD remains optional.
Exit criteria: installation without extras includes the maintained geometry
packages, `cadctx verify plate2d` succeeds, and required checks are recorded.

Open points: none; the requested default behavior is settled.
