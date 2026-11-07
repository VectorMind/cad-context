"""Shared fixtures.

Every test that touches the workspace redirects ``.cache/`` into ``tmp_path``
via ``CAD_CONTEXT_CACHE``, so a test run never writes into the developer's
real cache.
"""

from __future__ import annotations

import pytest

from cad_context import backends, project_catalog, workspace


@pytest.fixture(autouse=True)
def isolated_catalog(tmp_path, monkeypatch):
    """Tests must not discover or execute a developer's default model project."""
    monkeypatch.setattr(
        project_catalog, "catalog_path", lambda: tmp_path / "projects.yaml"
    )


@pytest.fixture()
def cache(tmp_path, monkeypatch):
    """Redirect the workspace cache into a temporary directory."""
    target = tmp_path / "cache"
    monkeypatch.setenv(workspace.CACHE_ENV_VAR, str(target))
    return target


def pytest_generate_tests(metafunc):
    """Parametrise a ``<family>_3d`` fixture over that family's installed backends.

    A test asking for ``bracket_3d`` runs once per 3D backend that builds the
    bracket. Naming the family is the point: generators of different families
    build different parts and have different reference values, so a test may
    only sweep one of them.
    """
    from cad_context import generators

    # Collection runs before fixtures, including on machines without Drive.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(project_catalog, "load", project_catalog.Catalog)
        for name in generators.families():
            fixture = f"{name}_3d"
            if fixture not in metafunc.fixturenames:
                continue
            metafunc.parametrize(
                fixture,
                [
                    spec.id
                    for spec in generators.family(name, kind="3d")
                    if backends.available(spec.backend)
                ],
            )
