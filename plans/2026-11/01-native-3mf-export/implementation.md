Progress: ■■■■■■ — implementation and native Windows acceptance complete.

2026-11-01. Read plan, 3MF/exchange/backend contracts and current exporter,
registry, project and verification surfaces. Preserving pre-existing changes.

Initial Linux uv commands failed on cache permissions; retry with a redirected
cache replaced the Windows .venv with an incomplete Linux environment. Moved
that environment to .cache/scratch/linux-venv and restored Windows .venv using
native uv sync --locked --extra default. No dependency or lock changes needed.
Native subprocess output requires Start-Process with redirected stdout/stderr
and explicit ExitCode; ordinary WSL child invocation yielded no uv output.
Native info/generators/paths now exit 0; only optional OpenSCAD is absent.

Inspected installed build123d 0.11.1 Mesher: explicit Unit.MM,
linear_deflection/angular_deflection parameters, fresh model per file. add_shape
adds an unused component resource in addition to one mesh/build item. Permit
that resource while validating its references; printable delivery remains one
mesh and one direct build item. No wrapper bypass needed.

Implemented exchange/three_mf.py, registered format kind/order and dispatch,
and added independent measurements to CLI results and project sidecars. Uses
exact-coordinate welding for adjacency only; never rounds vertices or repairs
faces/winding. Rejects extra shells/faces/wires as well as multiple solids.
Temporary artifacts are validated before atomic replacement even with
measure=False. Mesher runtime absence follows BackendUnavailable; geometry
RuntimeError becomes ValueError so it cannot be mistaken for an optional skip.

Verification now requires each selected/declared artifact, except optional
OpenSCAD renderer outputs. Added repeated --format/-f to verify so opt-in 3MF
can be proved without changing built-in defaults. This small extension to the
plan makes the existing generate format selection usable for verification.
Info reports exchange_formats; project manifests validate formats against kind
and restrict 3MF to build123d. No package/dependency changes made by this packet.

Added actual ZIP/XML mutation, topology, transform, independent lib3mf read,
atomic failure, malformed-writer, extra-wire, format validation and missing-file
regressions. Temporary external projects prove separate generator routing,
independent volumes, measurement sidecars and no project bytecode writes.

README plus 3MF, exchange, agent-interface, backend-policy and model-project
contracts updated in the same pass. No web source changes: the existing artifact
handler accepts arbitrary confined filenames and uses application/octet-stream
for unknown extensions, so 3MF downloads need no web implementation changes.
No web checks/build required under the packet's conditional obligation.

Commands performed: native uv sync --locked --extra default; native uv run
--extra default cadctx --no-project info/generators/paths; native Mesher smoke
script via explicit exchange.export; native uv run --extra default pytest;
native uv run --extra default ruff check .; targeted initial pytest/lint and
ruff format of new files. Full proof and CLI acceptance are recorded in test.md.
Initial lint identified a closure variable-shadowing bug; corrected before the
passing full suites. Initial targeted run loaded that earlier CLI and failed
one test; subsequent full suites pass. No unresolved design choices remain.

Final native acceptance: 103 pytest passed / 1 optional OpenSCAD skip; Ruff
clean; real 3MF generate succeeded and verify passed 16/16 checks. Plate,
airfoil, bracket and wing default verifications passed 7/7, 9/9, 8/8 and 8/8.
All commands exited 0. Packet closed; changes remain in the working tree.
