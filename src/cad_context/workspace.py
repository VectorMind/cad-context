"""Workspace layout.

Every execution writes below a single git-ignored ``.cache/`` directory:

``.cache/results/``
    One small machine- and human-readable summary per CLI command
    (``<command>.json`` + ``<command>.md``), overwritten on each run so the
    directory never grows unbounded. ``last.json`` / ``last.md`` always point
    at the most recent command.
``.cache/reports/``
    Long output that must not reach the console (subprocess logs, probe
    details, test transcripts).
``.cache/cad/``
    Generated geometry, at *fixed* paths: ``.cache/cad/<generator>/<generator>.<ext>``.
    Filenames are stable across runs so a viewer (or a browser tab) can keep
    pointing at the same URL while parameters are iterated.
``.cache/scratch/``
    Throwaway scripts (an agent probing the Python API, a one-off experiment).

Nothing here is ever committed; ``.cache/`` is git-ignored in full.
"""

from __future__ import annotations

import os
from pathlib import Path

CACHE_DIRNAME = ".cache"
TOOLS_DIRNAME = ".tools"
ROOT_ENV_VAR = "CAD_CONTEXT_ROOT"
CACHE_ENV_VAR = "CAD_CONTEXT_CACHE"

_MARKERS = ("pyproject.toml", ".git")


def repo_root() -> Path:
    """Locate the workspace root.

    ``CAD_CONTEXT_ROOT`` wins; otherwise walk up from the current directory
    looking for ``pyproject.toml`` / ``.git``; otherwise the package's own
    parent tree; otherwise the current directory.
    """
    env = os.environ.get(ROOT_ENV_VAR)
    if env:
        return Path(env).expanduser().resolve()
    for start in (Path.cwd(), Path(__file__).resolve()):
        for candidate in (start, *start.parents):
            if any((candidate / marker).exists() for marker in _MARKERS):
                return candidate
    return Path.cwd().resolve()


def cache_dir() -> Path:
    env = os.environ.get(CACHE_ENV_VAR)
    base = Path(env).expanduser().resolve() if env else repo_root() / CACHE_DIRNAME
    return base


def results_dir() -> Path:
    return cache_dir() / "results"


def reports_dir() -> Path:
    return cache_dir() / "reports"


def cad_dir() -> Path:
    return cache_dir() / "cad"


def scratch_dir() -> Path:
    return cache_dir() / "scratch"


def tools_dir() -> Path:
    return repo_root() / TOOLS_DIRNAME


def generator_dir(generator_id: str) -> Path:
    """Fixed output directory for one generator's geometry."""
    return cad_dir() / generator_id


def ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def rel(path: Path | str) -> str:
    """Display form: repo-relative with forward slashes, absolute if outside."""
    p = Path(path)
    try:
        return p.resolve().relative_to(repo_root()).as_posix()
    except ValueError:
        return p.as_posix()


def layout() -> dict[str, str]:
    """The workspace contract as plain data (consumed by ``cadctx paths``)."""
    return {
        "root": rel(repo_root()),
        "cache": rel(cache_dir()),
        "results": rel(results_dir()),
        "reports": rel(reports_dir()),
        "cad": rel(cad_dir()),
        "scratch": rel(scratch_dir()),
        "tools": rel(tools_dir()),
    }
