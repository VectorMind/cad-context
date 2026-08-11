"""Workspace layout and artifact declarations."""

from __future__ import annotations

import pytest

from cad_context import artifacts, backends, results, workspace

pytestmark = pytest.mark.usefixtures("cache")


def test_every_execution_path_lives_under_the_cache(cache):
    for directory in (
        workspace.results_dir(),
        workspace.reports_dir(),
        workspace.cad_dir(),
    ):
        assert cache in directory.parents or cache == directory


def test_result_files_are_written_as_json_and_markdown():
    result = results.Result(
        command="unit-test",
        summary="a summary",
        facts={"volume": 1234.5},
        files=["a/b.stl"],
        data={"nested": {"ok": True}},
    )
    json_path, md_path = results.save(result)
    assert json_path.exists() and md_path.exists()
    markdown = md_path.read_text(encoding="utf-8")
    assert "# unit-test" in markdown
    assert "a/b.stl" in markdown
    assert "1234" in markdown


def test_reports_land_in_the_reports_directory():
    rel = results.write_report("unit-test", "line\n" * 500)
    path = workspace.repo_root() / rel
    assert path.exists()
    assert path.parent == workspace.reports_dir()


def test_artifacts_config_declares_openscad_for_this_platform():
    declared = artifacts.declared()
    assert "openscad" in declared
    entry = declared["openscad"]
    assert entry["source"] in {"github-release", "url"}
    assert entry["install_dir"].startswith(".tools/")
    assert artifacts.platform_key() in entry["platforms"]


def test_artifact_status_reports_resolution():
    rows = {row["name"]: row for row in artifacts.status()}
    assert rows["openscad"]["platform_supported"] is True


def test_unknown_artifact_is_reported_clearly():
    with pytest.raises(artifacts.ArtifactError, match="unknown artifact"):
        artifacts.entry("not-a-tool")


def test_backend_status_covers_every_declared_backend():
    rows = {row["backend"] for row in backends.status()}
    assert rows == set(backends.BACKENDS)
