"""Command results: small files, quiet console.

Console discipline (binding, see ``specifications/workspace-layout/spec.md``):
a command prints a handful of lines — status, a few key facts, and the path of
the result file. Everything longer goes to ``.cache/reports/``. Anything a
caller might want to parse goes to ``.cache/results/<command>.json``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rich.console import Console

from . import workspace

MAX_CONSOLE_FACTS = 8

_STATUS_STYLE = {
    "ok": "green",
    "skipped": "yellow",
    "degraded": "yellow",
    "error": "red",
}


@dataclass
class Result:
    """One command's outcome."""

    command: str
    status: str = "ok"
    summary: str = ""
    facts: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    files: list[str] = field(default_factory=list)
    report: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "status": self.status,
            "summary": self.summary,
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "facts": self.facts,
            "files": self.files,
            "report": self.report,
            "notes": self.notes,
            "data": self.data,
        }


def _slug(command: str) -> str:
    return command.replace(" ", "-").replace("/", "-").replace(":", "-")


def _markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['command']}",
        "",
        f"- status: **{payload['status']}**",
        f"- time: {payload['timestamp']}",
    ]
    if payload["summary"]:
        lines += ["", payload["summary"]]
    if payload["facts"]:
        lines += ["", "## Facts", "", "| key | value |", "| --- | --- |"]
        lines += [f"| {k} | {_fmt(v)} |" for k, v in payload["facts"].items()]
    if payload["files"]:
        lines += ["", "## Files", ""]
        lines += [f"- `{f}`" for f in payload["files"]]
    if payload["notes"]:
        lines += ["", "## Notes", ""]
        lines += [f"- {n}" for n in payload["notes"]]
    if payload["report"]:
        lines += ["", f"Full report: `{payload['report']}`"]
    lines += [
        "",
        "## Data",
        "",
        "```json",
        json.dumps(payload["data"], indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    if isinstance(value, (list, tuple)):
        return ", ".join(_fmt(v) for v in value)
    return str(value)


def write_report(command: str, text: str) -> str:
    """Park long output in ``.cache/reports/`` and return its display path."""
    path = workspace.ensure(workspace.reports_dir()) / f"{_slug(command)}.log"
    path.write_text(text, encoding="utf-8")
    return workspace.rel(path)


def save(result: Result) -> tuple[Path, Path]:
    """Write ``<command>.json`` / ``.md`` plus the ``last.*`` pointers."""
    payload = result.to_dict()
    directory = workspace.ensure(workspace.results_dir())
    slug = _slug(result.command)
    json_path = directory / f"{slug}.json"
    md_path = directory / f"{slug}.md"
    json_text = json.dumps(payload, indent=2)
    md_text = _markdown(payload)
    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    (directory / "last.json").write_text(json_text, encoding="utf-8")
    (directory / "last.md").write_text(md_text, encoding="utf-8")
    return json_path, md_path


def emit(
    result: Result,
    console: Console | None = None,
    *,
    as_json: bool = False,
    quiet: bool = False,
) -> Path:
    """Persist a result and print the minimal console rendering of it."""
    json_path, _ = save(result)
    console = console or Console()
    if as_json:
        console.print_json(json.dumps(result.to_dict()))
        return json_path
    if quiet:
        console.print(workspace.rel(json_path), highlight=False, soft_wrap=True)
        return json_path

    style = _STATUS_STYLE.get(result.status, "white")
    head = f"[{style}]{result.status}[/{style}] [bold]{result.command}[/bold]"
    if result.summary:
        head += f" — {result.summary}"
    console.print(head, highlight=False, soft_wrap=True)
    for key, value in list(result.facts.items())[:MAX_CONSOLE_FACTS]:
        console.print(f"  {key}: {_fmt(value)}", highlight=False, soft_wrap=True)
    if result.files:
        shown = result.files[:3]
        extra = len(result.files) - len(shown)
        listed = ", ".join(shown) + (f" (+{extra} more)" if extra > 0 else "")
        console.print(f"  files: {listed}", highlight=False, soft_wrap=True)
    for note in result.notes[:2]:
        console.print(f"  note: {note}", highlight=False, soft_wrap=True)
    console.print(
        f"  result: {workspace.rel(json_path)}",
        style="dim",
        highlight=False,
        soft_wrap=True,
    )
    if result.report:
        console.print(
            f"  report: {result.report}", style="dim", highlight=False, soft_wrap=True
        )
    return json_path
