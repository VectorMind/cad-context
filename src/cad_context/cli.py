"""``cadcon`` — the single documented interface for humans and agents.

Console output stays minimal by contract: a status line, a few facts, and the
path of the result file. The full payload of every run is in
``.cache/results/<command>.json``; anything verbose is in ``.cache/reports/``.
"""

from __future__ import annotations

import shutil
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console

from . import (
    artifacts,
    backends,
    exchange,
    generators,
    project_catalog,
    projects,
    publication,
    results,
    web,
    workspace,
)
from .params import parse_overrides

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help=(
        "cad-context CLI — generate and verify project-oriented 2D/3D geometry. "
        "Operational output goes to .cache/; the console stays quiet."
    ),
)
project_app = typer.Typer(help="Initialize, select, inspect, or clear a model project.")
app.add_typer(project_app, name="project")
console = Console()

ParamOption = Annotated[
    list[str] | None,
    typer.Option("--param", "-p", help="Parameter override, repeatable: -p width=90"),
]
FormatOption = Annotated[
    list[str] | None,
    typer.Option("--format", "-f", help="Export format, repeatable (default: all)"),
]


@app.callback()
def main_options(
    ctx: typer.Context,
    json_out: Annotated[
        bool, typer.Option("--json", help="Print the result payload as JSON")
    ] = False,
    quiet: Annotated[
        bool, typer.Option("--quiet", "-q", help="Print only the result file path")
    ] = False,
    project: Annotated[
        Path | None,
        typer.Option(
            "--project",
            help="Use a catalog project ID or initialized project path",
        ),
    ] = None,
    no_project: Annotated[
        bool,
        typer.Option(
            "--no-project",
            help="Ignore all project selection, including the catalog default",
        ),
    ] = False,
) -> None:
    if project is not None and no_project:
        raise typer.BadParameter("--project and --no-project are mutually exclusive")
    projects.configure_command_project(project, disabled=no_project)
    ctx.obj = {"json": json_out, "quiet": quiet}


def _run(ctx: typer.Context, command: str, fn: Callable[[], results.Result]) -> None:
    """Execute a command body, emit its result, and map failures to exit code 1."""
    options = ctx.obj or {}
    try:
        result = fn()
    except Exception as exc:  # noqa: BLE001 - every failure becomes a result file
        report = results.write_report(command, traceback.format_exc())
        result = results.Result(
            command=command,
            status="error",
            summary=f"{type(exc).__name__}: {exc}".split("\n")[0][:200],
            report=report,
        )
        results.emit(result, console, as_json=options.get("json", False), quiet=False)
        raise typer.Exit(code=1) from None
    results.emit(
        result,
        console,
        as_json=options.get("json", False),
        quiet=options.get("quiet", False),
    )
    if result.status == "error":
        raise typer.Exit(code=1)


def _spec_params(generator_id: str, overrides: list[str] | None) -> Any:
    spec = generators.get(generator_id)
    return spec.parse(parse_overrides(list(overrides or [])))


@app.command()
def info(ctx: typer.Context) -> None:
    """Report Python, backend availability and external binaries."""

    def body() -> results.Result:
        rows = backends.status()
        tools = artifacts.status()
        ready = [r["backend"] for r in rows if r["available"]]
        missing = [r["backend"] for r in rows if not r["available"]]
        degraded = [r["backend"] for r in rows if r.get("degraded")]
        return results.Result(
            command="info",
            status="degraded" if (missing or degraded) else "ok",
            summary=f"{len(ready)}/{len(rows)} backends available",
            facts={
                "python": sys.version.split()[0],
                "active_project": workspace.layout()["active_project"],
                "backends_ready": ready,
                "backends_missing": missing or "none",
                "binaries": [
                    f"{t['name']}={'ok' if t['executable'] else 'absent'}"
                    for t in tools
                ],
            },
            notes=(
                [
                    f"{b}: python ok, binary absent — degrades to source-only output"
                    for b in degraded
                ]
            ),
            data={
                "backends": rows,
                "artifacts": tools,
                "paths": workspace.layout(),
                "exchange_formats": list(exchange.FORMAT_ORDER),
            },
        )

    _run(ctx, "info", body)


@app.command("generators")
def list_generators(ctx: typer.Context) -> None:
    """List every generator with its backend, kind and formats."""

    def body() -> results.Result:
        from . import api

        rows = api.generators()
        return results.Result(
            command="generators",
            status="ok",
            summary=f"{len(rows)} generators",
            facts={
                r["id"]: f"{r['backend']} · {r['kind']} · "
                f"{'ready' if r['available'] else 'unavailable'}"
                for r in rows
            },
            data={"generators": rows},
        )

    _run(ctx, "generators", body)


@app.command()
def schema(
    ctx: typer.Context,
    generator: Annotated[
        str, typer.Argument(help="Generator id (see `cadcon generators`)")
    ],
) -> None:
    """Print a generator's parameter schema (the web-app control contract)."""

    def body() -> results.Result:
        payload = generators.get(generator).schema()
        return results.Result(
            command=f"schema-{generator}",
            status="ok",
            summary=f"{len(payload['parameters'])} parameters",
            facts={
                str(p["name"]): (
                    f"{p['default']} [{p['minimum']}..{p['maximum']}] {p['unit']}"
                )
                for p in payload["parameters"]
            },
            data=payload,
        )

    _run(ctx, f"schema-{generator}", body)


@app.command()
def generate(
    ctx: typer.Context,
    generator: Annotated[str, typer.Argument(help="Generator id")],
    param: ParamOption = None,
    fmt: FormatOption = None,
    out_dir: Annotated[
        Path | None,
        typer.Option("--out-dir", help="Override the generator's fixed artifact path"),
    ] = None,
    measure: Annotated[
        bool,
        typer.Option("--measure/--no-measure", help="Load exports back and measure"),
    ] = True,
) -> None:
    """Generate one shape and export it to its fixed artifact root."""

    def body() -> results.Result:
        spec = generators.get(generator)
        params = _spec_params(generator, param)
        build_result = spec.build(params)
        formats = list(fmt) if fmt else list(spec.formats)
        exported = exchange.export(
            build_result, formats, out_dir=out_dir, measure=measure
        )
        facts: dict[str, Any] = {"backend": spec.backend}
        for key in ("volume", "volume_analytic", "area"):
            if key in build_result.metrics:
                facts[key] = build_result.metrics[key]
        mesh = exported["measurements"].get("mesh")
        if mesh:
            facts["mesh_volume"] = mesh["volume"]
            facts["watertight"] = mesh["watertight"]
        status = "degraded" if exported["skipped"] else "ok"
        files = [workspace.rel(p) for p in exported["files"].values()]
        if exported["measurement_file"] is not None:
            files.append(workspace.rel(exported["measurement_file"]))
        return results.Result(
            command=f"generate-{generator}",
            status=status,
            summary=f"{len(exported['files'])} artifact(s) from {spec.backend}",
            facts=facts,
            files=files,
            notes=[f"skipped {k}: {v}" for k, v in exported["skipped"].items()],
            data={
                "params": params.model_dump(),
                "metrics": build_result.metrics,
                "files": {k: workspace.rel(v) for k, v in exported["files"].items()},
                "measurements": exported["measurements"],
                "skipped": exported["skipped"],
                "measurement_file": (
                    workspace.rel(exported["measurement_file"])
                    if exported["measurement_file"] is not None
                    else None
                ),
            },
        )

    _run(ctx, f"generate-{generator}", body)


@app.command()
def demo(
    ctx: typer.Context,
    only: Annotated[
        str | None, typer.Option("--only", help="Restrict to one backend")
    ] = None,
    param: ParamOption = None,
) -> None:
    """Run every available generator with defaults (or -p overrides)."""

    def body() -> results.Result:
        overrides = parse_overrides(list(param or []))
        runs: dict[str, Any] = {}
        files: list[str] = []
        notes: list[str] = []
        for spec in generators.specs():
            if only and spec.backend != only:
                continue
            if not backends.available(spec.backend):
                runs[spec.id] = {"status": "unavailable", "backend": spec.backend}
                notes.append(f"{spec.id}: backend {spec.backend} not installed")
                continue
            build_result = spec.build(
                {
                    k: v
                    for k, v in overrides.items()
                    if k in spec.parameter_model().model_fields
                }
            )
            exported = exchange.export(build_result, list(spec.formats))
            files += [workspace.rel(p) for p in exported["files"].values()]
            runs[spec.id] = {
                "status": "degraded" if exported["skipped"] else "ok",
                "backend": spec.backend,
                "metrics": build_result.metrics,
                "files": {k: workspace.rel(v) for k, v in exported["files"].items()},
                "measurements": exported["measurements"],
                "skipped": exported["skipped"],
            }
            notes += [f"{spec.id} skipped {k}" for k in exported["skipped"]]
        ok = sum(1 for r in runs.values() if r["status"] == "ok")
        return results.Result(
            command="demo",
            status="ok" if ok == len(runs) else "degraded",
            summary=f"{ok}/{len(runs)} generators clean, {len(files)} artifacts",
            facts={gid: f"{r['status']} ({r['backend']})" for gid, r in runs.items()},
            files=files,
            notes=notes,
            data={"runs": runs, "params": overrides},
        )

    _run(ctx, "demo", body)


@app.command()
def verify(
    ctx: typer.Context,
    generator: Annotated[str, typer.Argument(help="Generator id")],
    param: ParamOption = None,
    fmt: FormatOption = None,
    tolerance: Annotated[
        float,
        typer.Option(
            "--tolerance",
            help="Relative tolerance for tessellated or approximate references",
        ),
    ] = 0.01,
) -> None:
    """Prove one generator against its analytic and exchange-format contracts."""

    def body() -> results.Result:
        spec = generators.get(generator)
        overrides = parse_overrides(list(param or []))
        params = spec.parse(overrides)
        build_result = spec.build(params)
        formats = list(fmt) if fmt else list(spec.formats)
        exported = exchange.export(build_result, formats, measure=True)
        metrics = build_result.metrics
        reference_key = "area_analytic" if spec.kind == "2d" else "volume_analytic"
        native_key = "area" if spec.kind == "2d" else "volume"
        reference = metrics.get(reference_key)
        native = metrics.get(native_key)
        exact_reference = bool(metrics.get("reference_exact", spec.kind == "3d"))
        native_tolerance = 1e-6 if exact_reference and spec.kind == "3d" else tolerance

        def close(actual: Any, expected: Any, allowed: float) -> bool:
            if actual is None or expected in (None, 0):
                return False
            deviation = abs(float(actual) - float(expected)) / abs(float(expected))
            return deviation <= allowed

        checks: dict[str, bool] = {"analytic_reference_present": reference is not None}
        if native is not None:
            checks["native_matches_analytic"] = close(
                native, reference, native_tolerance
            )
        # OpenSCAD's external renderer is optional. Declared B-rep artifacts
        # remain required even when a runtime dependency is unavailable.
        for selected_format in formats:
            optional = spec.backend == "openscad" and selected_format in {"stl", "glb"}
            if not optional:
                checks[f"{selected_format}_artifact_present"] = (
                    selected_format in exported["files"]
                )
        measured = exported["measurements"]
        if "3mf" in measured:
            mesh3mf = measured["3mf"]
            checks.update({f"3mf_{k}": v for k, v in mesh3mf["checks"].items()})
            checks["3mf_matches_reference"] = close(
                mesh3mf["volume"], reference, min(tolerance, 0.01)
            )
            checks["3mf_matches_native"] = close(
                mesh3mf["volume"], native, min(tolerance, 0.01)
            )
            from .exchange.three_mf import bounds_match

            for key in ("bounds_min", "bounds_max"):
                checks[f"3mf_{key}_matches_native"] = bool(
                    key in metrics
                    and bounds_match(
                        mesh3mf[key],
                        metrics[key],
                        metrics["bounds_min"],
                        metrics["bounds_max"],
                    )
                )
        if "mesh" in measured:
            mesh = measured["mesh"]
            checks["mesh_watertight"] = bool(mesh["watertight"])
            checks["mesh_matches_reference"] = close(
                mesh["volume"], reference, tolerance
            )
        if "step" in measured:
            checks["step_matches_native"] = close(
                measured["step"]["volume"], native, 1e-6
            )
        if "dxf" in measured:
            checks["dxf_units_mm"] = measured["dxf"]["units_name"] == "mm"
            checks["dxf_has_geometry"] = measured["dxf"]["vertices"] > 0
        if "svg" in measured:
            checks["svg_has_geometry"] = bool(
                measured["svg"]["has_viewbox"] and measured["svg"]["paths"]
            )
        if "json" in measured:
            checks["json_has_geometry"] = bool(
                measured["json"]["points"] and measured["json"]["units"] == "mm"
            )

        failed = [name for name, passed in checks.items() if not passed]
        notes = [f"skipped {fmt}: {why}" for fmt, why in exported["skipped"].items()]
        if not exact_reference:
            notes.append("analytic reference is approximate for these parameters")
        status = "error" if failed else ("degraded" if exported["skipped"] else "ok")
        files = [workspace.rel(path) for path in exported["files"].values()]
        if exported["measurement_file"] is not None:
            files.append(workspace.rel(exported["measurement_file"]))
        return results.Result(
            command=f"verify-{generator}",
            status=status,
            summary=f"{len(checks) - len(failed)}/{len(checks)} checks passed",
            facts={
                "backend": spec.backend,
                "reference": reference,
                "native": native,
                "checks_passed": len(checks) - len(failed),
                "checks_failed": len(failed),
            },
            files=files,
            notes=notes,
            data={
                "generator": generator,
                "kind": spec.kind,
                "params": params.model_dump(),
                "reference": reference,
                "native": native,
                "reference_exact": exact_reference,
                "tolerance": tolerance,
                "checks": checks,
                "measurements": measured,
                "files": {
                    fmt: workspace.rel(path) for fmt, path in exported["files"].items()
                },
                "skipped": exported["skipped"],
            },
        )

    _run(ctx, f"verify-{generator}", body)


@app.command()
def fetch(
    ctx: typer.Context,
    name: Annotated[
        str | None, typer.Argument(help="Artifact name, e.g. openscad")
    ] = None,
    all_: Annotated[
        bool, typer.Option("--all", help="Fetch every declared artifact")
    ] = False,
    list_: Annotated[
        bool, typer.Option("--list", help="List declared artifacts only")
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", help="Re-download and replace")
    ] = False,
) -> None:
    """Provision external binaries declared in config/artifacts.yaml into .tools/."""

    def body() -> results.Result:
        if list_ or (not name and not all_):
            rows = artifacts.status()
            return results.Result(
                command="fetch-list",
                status="ok",
                summary=f"{len(rows)} declared artifact(s)",
                facts={r["name"]: r["executable"] or "not installed" for r in rows},
                data={"artifacts": rows, "platform": artifacts.platform_key()},
            )
        names = list(artifacts.declared()) if all_ else [name or ""]
        outcomes: dict[str, Any] = {}
        log_lines: list[str] = []
        for artifact_name in names:
            fetched = artifacts.fetch(artifact_name, force=force)
            log_lines += [f"[{artifact_name}] {line}" for line in fetched.log]
            outcomes[artifact_name] = {
                "status": fetched.status,
                "executable": str(fetched.executable) if fetched.executable else None,
                "asset": fetched.asset,
                "url": fetched.url,
            }
        report = results.write_report("fetch", "\n".join(log_lines))
        bad = [n for n, o in outcomes.items() if o["status"] == "unavailable"]
        return results.Result(
            command="fetch",
            status="degraded" if bad else "ok",
            summary=", ".join(f"{n}: {o['status']}" for n, o in outcomes.items()),
            facts={
                n: workspace.rel(o["executable"]) if o["executable"] else "unavailable"
                for n, o in outcomes.items()
            },
            report=report,
            data={"artifacts": outcomes, "platform": artifacts.platform_key()},
        )

    _run(ctx, "fetch", body)


@project_app.command("init")
def project_init(
    ctx: typer.Context,
    path: Annotated[Path, typer.Argument(help="Folder to initialize")],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Report the scaffold without writing it"),
    ] = False,
) -> None:
    """Initialize a project folder without overwriting an existing manifest."""

    def body() -> results.Result:
        payload = projects.initialise(path, dry_run=dry_run)
        return results.Result(
            command="project-init",
            status="ok",
            summary=("project scaffold preview" if dry_run else "project initialized"),
            facts={"project": payload["project"], "dry_run": dry_run},
            files=[] if dry_run else [payload["manifest"]],
            data=payload,
        )

    _run(ctx, "project-init", body)


@project_app.command("use")
def project_use(
    ctx: typer.Context,
    path: Annotated[
        Path, typer.Argument(help="Catalog ID or initialized project folder")
    ],
) -> None:
    """Persist the active project for subsequent commands."""

    def body() -> results.Result:
        selected = projects.persist(path)
        payload = projects.describe(selected)
        return results.Result(
            command="project-use",
            status="ok",
            summary=f"active project: {payload['name']}",
            facts={"project": str(selected)},
            data=payload,
        )

    _run(ctx, "project-use", body)


@project_app.command("root")
def project_root(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Root name in config/projects.yaml")],
    path: Annotated[Path, typer.Argument(help="This machine's project parent folder")],
) -> None:
    """Bind a portable storage root locally; never modifies the shared catalog."""

    def body() -> results.Result:
        resolved = project_catalog.bind(name, path)
        return results.Result(
            command="project-root",
            summary=f"bound root: {name}",
            facts={"root": name, "path": str(resolved)},
            files=[str(project_catalog.local_path())],
            data={"root": name, "path": str(resolved)},
        )

    _run(ctx, "project-root", body)


@project_app.command("list")
def project_list(ctx: typer.Context) -> None:
    """List catalog projects and immediate child project manifests in each root."""

    def body() -> results.Result:
        payload = project_catalog.listing()
        rows = payload["projects"]
        return results.Result(
            command="project-list",
            summary=f"{len(rows)} projects",
            facts={
                row["id"] or row["path"]: (
                    "available" if row["available"] else "unavailable"
                )
                + (" (default)" if row["default"] else "")
                for row in rows
            },
            data=payload,
        )

    _run(ctx, "project-list", body)


@project_app.command("clear")
def project_clear(ctx: typer.Context) -> None:
    """Clear the persisted project pointer."""

    def body() -> results.Result:
        removed = projects.clear()
        return results.Result(
            command="project-clear",
            status="ok",
            summary="active project cleared" if removed else "no persisted project",
            facts={"removed": removed},
            data={"removed": removed},
        )

    _run(ctx, "project-clear", body)


@project_app.command("info")
def project_info(ctx: typer.Context) -> None:
    """Report the active project without importing generator modules."""

    def body() -> results.Result:
        payload = projects.describe()
        return results.Result(
            command="project-info",
            status="ok",
            summary=(
                f"active project: {payload['name']}"
                if payload["active"]
                else "repository mode"
            ),
            facts={
                "active": payload["active"],
                "project": payload.get("project") or "none",
            },
            data=payload,
        )

    _run(ctx, "project-info", body)


def _publication_result(command: str, payload: dict) -> results.Result:
    return results.Result(
        command=command,
        summary=command.replace("-", " "),
        facts={"project": payload.get("project_id", payload.get("id", ""))},
        data=payload,
    )


@project_app.command("view")
def project_view(ctx: typer.Context, project_id: str) -> None:
    """Read published project metadata without importing or building source."""
    _run(
        ctx,
        "project-view",
        lambda: _publication_result("project-view", publication.view(project_id)),
    )


@project_app.command("snapshot")
def project_snapshot(ctx: typer.Context, project_id: str) -> None:
    """Save portable source/reference recovery data; no generated geometry."""
    _run(
        ctx,
        "project-snapshot",
        lambda: _publication_result(
            "project-snapshot", publication.snapshot(project_id)
        ),
    )


@project_app.command("restore")
def project_restore(ctx: typer.Context, project_id: str, destination: Path) -> None:
    """Restore source to a new folder; never overwrite existing local edits."""
    _run(
        ctx,
        "project-restore",
        lambda: _publication_result(
            "project-restore", publication.restore(project_id, destination)
        ),
    )


@project_app.command("rebuild")
def project_rebuild(
    ctx: typer.Context,
    reuse_exports: Annotated[bool, typer.Option("--reuse-exports")] = False,
) -> None:
    """Recreate and verify the active project's disposable local working outputs."""

    def body():
        root = projects.active_path()
        if root is None:
            raise projects.ProjectError("select a project before rebuilding")
        return _publication_result(
            "project-rebuild", publication.rebuild(root, reuse_exports=reuse_exports)
        )

    _run(ctx, "project-rebuild", body)


@project_app.command("publish")
def project_publish(ctx: typer.Context, project_id: str) -> None:
    """Publish verified GLBs and source snapshot; never creates a print release."""
    _run(
        ctx,
        "project-publish",
        lambda: _publication_result("project-publish", publication.publish(project_id)),
    )


@project_app.command("present")
def project_present(ctx: typer.Context, project_id: str) -> None:
    """Publish visual stages from presentation.yaml without changing geometry."""
    from . import presentation

    _run(
        ctx,
        "project-present",
        lambda: _publication_result(
            "project-present", presentation.present(project_id)
        ),
    )


@project_app.command("release")
def project_release(
    ctx: typer.Context,
    project_id: str,
    date: str,
    freeze: Annotated[bool, typer.Option("--freeze")] = False,
) -> None:
    """Explicitly create a dated individual-piece 3MF package."""
    _run(
        ctx,
        "project-release",
        lambda: _publication_result(
            "project-release", publication.release(project_id, date, freeze=freeze)
        ),
    )


@project_app.command("freeze")
def project_freeze(ctx: typer.Context, project_id: str, date: str) -> None:
    """Verify checksums and freeze an existing dated print package."""
    _run(
        ctx,
        "project-freeze",
        lambda: _publication_result(
            "project-freeze", publication.freeze(project_id, date)
        ),
    )


@app.command("web")
def web_command(
    ctx: typer.Context,
    port: Annotated[int, typer.Option("--port", help="Port to serve on")] = 4321,
    host: Annotated[
        str, typer.Option("--host", help="Interface to bind")
    ] = "127.0.0.1",
    install: Annotated[
        bool,
        typer.Option("--install/--no-install", help="Run pnpm install when needed"),
    ] = True,
    open_browser: Annotated[
        bool, typer.Option("--open", help="Open the app in a browser once it is up")
    ] = False,
) -> None:
    """Serve the shape viewer web app; its pages call this CLI per request."""
    server: dict[str, Any] = {}

    def body() -> results.Result:
        directory = web.webapp_dir()
        log = workspace.ensure(workspace.reports_dir()) / "web.log"
        if install and not web.dependencies_installed(directory):
            web.install(directory, log)
        rows = backends.status()
        ready = [r["backend"] for r in rows if r["available"]]
        missing = [r["backend"] for r in rows if not r["available"]]
        active_project = projects.active_path()
        started = web.start(
            directory,
            log,
            host=host,
            port=port,
            project=active_project,
        )
        server["handle"] = started
        return results.Result(
            command="web",
            status="degraded" if missing else "ok",
            summary=f"serving {started.url} ({len(ready)}/{len(rows)} backends ready)",
            facts={
                "url": started.url,
                "webapp": workspace.rel(directory),
                "backends_ready": ready,
                "backends_missing": missing or "none",
                "active_project": str(active_project) if active_project else "none",
                "generators": f"{started.url}api/generators.json",
            },
            report=workspace.rel(log),
            notes=[
                "stop with Ctrl-C; the dev server log is in the report file",
                *(f"{b}: backend not installed, its pages stay empty" for b in missing),
            ],
            data={
                "url": started.url,
                "pid": started.process.pid,
                "webapp": workspace.rel(directory),
                "log": workspace.rel(log),
                "backends": rows,
                "active_project": str(active_project) if active_project else None,
            },
        )

    _run(ctx, "web", body)
    handle: web.DevServer | None = server.get("handle")
    if handle is None:  # pragma: no cover - body always sets it on success
        return
    if open_browser:
        import webbrowser

        webbrowser.open(handle.url)
    raise typer.Exit(code=handle.wait())


@app.command()
def paths(ctx: typer.Context) -> None:
    """Print operational, project, and fixed per-generator paths."""

    def body() -> results.Result:
        layout = workspace.layout()
        return results.Result(
            command="paths",
            status="ok",
            summary="workspace layout",
            facts=layout,
            data={
                "layout": layout,
                "cad_files": {
                    spec.id: {
                        f: workspace.rel(exchange.destination(spec.id, f))
                        for f in spec.formats
                    }
                    for spec in generators.specs()
                },
            },
        )

    _run(ctx, "paths", body)


@app.command()
def clean(
    ctx: typer.Context,
    what: Annotated[
        str,
        typer.Option(
            "--what", help="all | results | reports | cad | scratch | downloads"
        ),
    ] = "all",
) -> None:
    """Delete generated content under .cache/."""

    def body() -> results.Result:
        targets = {
            "results": workspace.results_dir(),
            "reports": workspace.reports_dir(),
            "cad": workspace.cad_dir(),
            "scratch": workspace.scratch_dir(),
            "downloads": workspace.cache_dir() / "downloads",
        }
        selected = targets if what == "all" else {what: targets[what]}
        removed = []
        for label, directory in selected.items():
            if directory.exists():
                shutil.rmtree(directory)
                removed.append(label)
        return results.Result(
            command="clean",
            status="ok",
            summary=f"removed {', '.join(removed) if removed else 'nothing'}",
            facts={
                "removed": removed or "none",
                "cache": workspace.rel(workspace.cache_dir()),
            },
            data={"removed": removed},
        )

    _run(ctx, "clean", body)


def main() -> None:
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
