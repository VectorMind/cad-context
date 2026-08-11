"""CLI contract: result files always, console output always small."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from cad_context import workspace
from cad_context.cli import app

#: The console-quietness budget from the workspace-layout spec.
MAX_CONSOLE_LINES = 14

runner = CliRunner()
pytestmark = pytest.mark.usefixtures("cache")


def run(*args):
    result = runner.invoke(app, list(args))
    assert result.exit_code == 0, result.output
    return result


def result_payload(command: str) -> dict:
    path = workspace.results_dir() / f"{command}.json"
    assert path.exists(), f"missing result file for {command}"
    return json.loads(path.read_text(encoding="utf-8"))


def console_lines(output: str) -> list[str]:
    return [line for line in output.splitlines() if line.strip()]


@pytest.mark.parametrize(
    ("args", "command"),
    [
        (("info",), "info"),
        (("generators",), "generators"),
        (("paths",), "paths"),
        (("schema", "bracket-cadquery"), "schema-bracket-cadquery"),
        (("fetch", "--list"), "fetch-list"),
    ],
)
def test_read_only_commands_write_a_result_and_stay_quiet(args, command):
    result = run(*args)
    assert len(console_lines(result.output)) <= MAX_CONSOLE_LINES
    payload = result_payload(command)
    assert payload["command"] == command
    assert payload["status"] in {"ok", "degraded"}
    assert (workspace.results_dir() / f"{command}.md").exists()


def test_last_pointer_tracks_the_most_recent_command():
    run("paths")
    last = json.loads(
        (workspace.results_dir() / "last.json").read_text(encoding="utf-8")
    )
    assert last["command"] == "paths"


def test_json_and_quiet_modes():
    quiet = run("--quiet", "paths")
    assert console_lines(quiet.output) == [
        workspace.rel(workspace.results_dir() / "paths.json")
    ]

    as_json = run("--json", "generators")
    payload = json.loads(as_json.output)
    assert payload["command"] == "generators"
    assert len(payload["data"]["generators"]) >= 4


def test_generate_writes_to_the_fixed_cad_path():
    run("generate", "plate2d", "-p", "width=140", "-f", "svg", "-f", "dxf")
    payload = result_payload("generate-plate2d")
    assert payload["status"] == "ok"
    assert payload["data"]["params"]["width"] == 140.0
    for fmt in ("svg", "dxf"):
        path = workspace.cad_dir() / "plate2d" / f"plate2d.{fmt}"
        assert path.exists()
        assert payload["data"]["files"][fmt] == workspace.rel(path)


def test_regenerating_reuses_the_same_paths():
    run("generate", "plate2d", "-f", "svg")
    first = result_payload("generate-plate2d")["data"]["files"]
    run("generate", "plate2d", "-p", "width=200", "-f", "svg")
    second = result_payload("generate-plate2d")["data"]["files"]
    assert first == second  # a viewer can keep pointing at one URL


def test_compare_reports_cross_backend_agreement():
    run("compare", "--no-meshes")
    payload = result_payload("compare-bracket")
    assert payload["data"]["within_tolerance"] is True
    assert payload["data"]["max_deviation"] < 0.01


def test_bad_parameter_fails_with_a_result_file_and_exit_code():
    result = runner.invoke(app, ["generate", "plate2d", "-p", "width=-5"])
    assert result.exit_code == 1
    payload = result_payload("generate-plate2d")
    assert payload["status"] == "error"
    assert payload["report"]
    assert (workspace.repo_root() / payload["report"]).exists()
    assert len(console_lines(result.output)) <= 4


def test_unknown_generator_fails_cleanly():
    result = runner.invoke(app, ["generate", "nope"])
    assert result.exit_code == 1
    assert "unknown generator" in result.output


def test_clean_removes_cache_subdirectories():
    run("generate", "plate2d", "-f", "svg")
    assert workspace.cad_dir().exists()
    run("clean", "--what", "cad")
    assert not workspace.cad_dir().exists()
    assert result_payload("clean")["data"]["removed"] == ["cad"]
