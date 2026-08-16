"""Web-app command contract: locate the app, degrade with a usable message.

Starting a real dev server belongs in the packet's ``test.md`` (it needs Node
and a port); what is unit-testable is everything around it.
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from cad_context import web, workspace
from cad_context.cli import app

runner = CliRunner()
pytestmark = pytest.mark.usefixtures("cache")


def test_webapp_dir_is_the_webapp_folder_of_the_workspace():
    directory = web.webapp_dir()
    assert directory == workspace.repo_root() / "webapp"
    assert (directory / "package.json").exists()
    assert (directory / "config" / "exposure.json").exists()


def test_missing_webapp_is_an_error_result_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.setenv(workspace.ROOT_ENV_VAR, str(tmp_path))
    with pytest.raises(web.WebAppError):
        web.webapp_dir()

    result = runner.invoke(app, ["web"])
    assert result.exit_code == 1
    payload = json.loads(
        (workspace.results_dir() / "web.json").read_text(encoding="utf-8")
    )
    assert payload["status"] == "error"
    assert "webapp" in payload["summary"]


def test_dependency_probe_looks_for_the_installed_framework(tmp_path):
    assert not web.dependencies_installed(tmp_path)
    (tmp_path / "node_modules" / "astro").mkdir(parents=True)
    assert web.dependencies_installed(tmp_path)


def test_package_manager_falls_back_to_corepack(monkeypatch):
    def which(name):
        return None if name == "pnpm" else "C:/tools/corepack.cmd"

    monkeypatch.setattr(web.shutil, "which", which)
    assert web.package_manager() == ("C:/tools/corepack.cmd", "pnpm")
