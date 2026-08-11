# Open Plans

Plan packets with work still outstanding. See each folder for details.

_None._ The last open packet, [Airfoil Parametric
Visualizer](./2026-08/11-airfoil-parametric-visualizer/plan.md), landed on
2026-08-11 and moved to [closed.md](./closed.md).

Carried forward as the next candidate rather than as an open packet: the
OP-204 escalation from a per-request `cadctx` subprocess to a warm worker.
Regeneration of a B-rep shape now costs 2.3–3.5 s for the bracket and
3.8–6.1 s for the wing loft, nearly all of it process startup and the OCCT
import — the loft itself is ~0.15 s.
