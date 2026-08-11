"""Shared fixtures.

Every test that touches the workspace redirects ``.cache/`` into ``tmp_path``
via ``CAD_CONTEXT_CACHE``, so a test run never writes into the developer's
real cache.
"""

from __future__ import annotations

import pytest

from cad_context import backends, workspace


@pytest.fixture()
def cache(tmp_path, monkeypatch):
    """Redirect the workspace cache into a temporary directory."""
    target = tmp_path / "cache"
    monkeypatch.setenv(workspace.CACHE_ENV_VAR, str(target))
    return target


def pytest_generate_tests(metafunc):
    """Parametrise ``backend_3d`` over the 3D backends that are installed."""
    if "generator_3d" in metafunc.fixturenames:
        from cad_context import generators

        ids = [
            spec.id
            for spec in generators.SPECS
            if spec.kind == "3d" and backends.available(spec.backend)
        ]
        metafunc.parametrize("generator_3d", ids)
