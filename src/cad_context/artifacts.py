"""External binaries as declared artifacts.

``config/artifacts.yaml`` declares every external tool the repository may use.
:func:`fetch` downloads, verifies and unpacks one into ``.tools/<name>/``;
:func:`resolve_executable` finds it again at runtime (``.tools/`` first, then
``PATH``). Nothing here is installed system-wide, and ``.tools/`` is
git-ignored.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import stat
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import workspace

CONFIG_RELPATH = Path("config") / "artifacts.yaml"
GITHUB_API = "https://api.github.com/repos/{repo}/releases/tags/{tag}"
USER_AGENT = "cad-context/0.1 (+cadctx fetch)"
DOWNLOAD_TIMEOUT = 300


class ArtifactError(RuntimeError):
    """Configuration or download problem for a declared artifact."""


@dataclass
class FetchResult:
    name: str
    status: str  # "installed" | "cached" | "unavailable"
    executable: Path | None = None
    asset: str | None = None
    url: str | None = None
    install_dir: Path | None = None
    log: list[str] = field(default_factory=list)


def config_path() -> Path:
    return workspace.repo_root() / CONFIG_RELPATH


def load_config(path: Path | None = None) -> dict[str, Any]:
    import yaml

    target = path or config_path()
    if not target.exists():
        raise ArtifactError(f"artifact config not found: {workspace.rel(target)}")
    data = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    if "artifacts" not in data:
        raise ArtifactError(f"{workspace.rel(target)} has no `artifacts` section")
    return data


def platform_key() -> str:
    machine = platform.machine().lower()
    arch = {
        "amd64": "amd64",
        "x86_64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine, machine)
    return f"{sys.platform}-{arch}"


def declared(path: Path | None = None) -> dict[str, dict[str, Any]]:
    return load_config(path)["artifacts"]


def entry(name: str, path: Path | None = None) -> dict[str, Any]:
    artifacts = declared(path)
    if name not in artifacts:
        known = ", ".join(artifacts)
        raise ArtifactError(f"unknown artifact {name!r}; declared: {known}")
    return artifacts[name]


def install_dir(name: str, path: Path | None = None) -> Path:
    spec = entry(name, path)
    return workspace.repo_root() / spec.get("install_dir", f".tools/{name}")


def _executable_patterns(spec: dict[str, Any]) -> list[str]:
    platforms = spec.get("platforms", {})
    current = platforms.get(platform_key(), {})
    pattern = current.get("executable")
    return [pattern] if pattern else []


def resolve_executable(name: str, path: Path | None = None) -> Path | None:
    """Find a previously fetched binary, else fall back to ``PATH``."""
    try:
        spec = entry(name, path)
    except ArtifactError:
        spec = {}
    directory = (
        workspace.repo_root() / spec.get("install_dir", f".tools/{name}")
        if spec
        else workspace.tools_dir() / name
    )
    if directory.exists():
        for pattern in _executable_patterns(spec) or ["**/*"]:
            for candidate in sorted(directory.glob(pattern)):
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    return candidate
    found = shutil.which(name)
    return Path(found) if found else None


def _download(url: str, dest: Path, log: list[str]) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    log.append(f"GET {url}")
    with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
        payload = response.read()
    dest.write_bytes(payload)
    log.append(f"wrote {len(payload)} bytes to {dest}")
    return dest


def _github_asset(repo: str, tag: str, pattern: str, log: list[str]) -> tuple[str, str]:
    from fnmatch import fnmatch

    url = GITHUB_API.format(repo=repo, tag=tag)
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    )
    log.append(f"GET {url}")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
            release = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ArtifactError(f"GitHub API {exc.code} for {repo}@{tag}") from exc
    assets = release.get("assets", [])
    log.append(f"release {tag}: {len(assets)} assets")
    for asset in assets:
        if fnmatch(asset["name"], pattern):
            log.append(f"matched asset {asset['name']}")
            return asset["name"], asset["browser_download_url"]
    names = ", ".join(a["name"] for a in assets[:20])
    raise ArtifactError(f"no asset matching {pattern!r} in {repo}@{tag}; saw: {names}")


def _unpack(archive: Path, kind: str, dest: Path, log: list[str]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if kind == "zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
        log.append(f"unzipped into {dest}")
    elif kind in {"tar", "tar.gz", "tgz"}:
        with tarfile.open(archive) as tf:
            tf.extractall(dest)
        log.append(f"untarred into {dest}")
    elif kind == "none":
        target = dest / archive.name
        if target.resolve() != archive.resolve():
            shutil.copy2(archive, target)
        target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
        log.append(f"kept {target} as-is (executable)")
    else:
        raise ArtifactError(f"unsupported archive kind {kind!r}")


def fetch(name: str, *, force: bool = False, path: Path | None = None) -> FetchResult:
    """Provision one declared artifact into ``.tools/``."""
    log: list[str] = []
    spec = entry(name, path)
    target_dir = install_dir(name, path)
    key = platform_key()
    platforms = spec.get("platforms", {})
    if key not in platforms:
        return FetchResult(
            name=name,
            status="unavailable",
            install_dir=target_dir,
            log=[f"no entry for platform {key}; declared: {', '.join(platforms)}"],
        )

    existing = resolve_executable(name, path)
    if existing and not force and target_dir in existing.parents:
        return FetchResult(
            name=name,
            status="cached",
            executable=existing,
            install_dir=target_dir,
            log=[f"already installed at {existing}"],
        )

    platform_spec = platforms[key]
    source = spec.get("source", "github-release")
    if source == "github-release":
        asset_name, url = _github_asset(
            spec["repo"], str(spec["tag"]), platform_spec["pattern"], log
        )
    elif source == "url":
        url = platform_spec["url"]
        asset_name = url.rsplit("/", 1)[-1]
    else:
        raise ArtifactError(f"unsupported source {source!r} for artifact {name!r}")

    downloads = workspace.ensure(workspace.cache_dir() / "downloads")
    archive = _download(url, downloads / asset_name, log)

    expected = platform_spec.get("sha256")
    if expected:
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest != expected:
            raise ArtifactError(f"sha256 mismatch for {asset_name}: {digest}")
        log.append("sha256 verified")

    if force and target_dir.exists():
        shutil.rmtree(target_dir)
    _unpack(archive, platform_spec.get("archive", "zip"), target_dir, log)

    executable = resolve_executable(name, path)
    if executable is None:
        raise ArtifactError(
            f"unpacked {asset_name} but no executable matched "
            f"{platform_spec.get('executable')!r} under {workspace.rel(target_dir)}"
        )
    if os.name != "nt":
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    log.append(f"executable: {executable}")
    return FetchResult(
        name=name,
        status="installed",
        executable=executable,
        asset=asset_name,
        url=url,
        install_dir=target_dir,
        log=log,
    )


def status(path: Path | None = None) -> list[dict[str, Any]]:
    """One row per declared artifact, for ``cadctx info`` / ``cadctx fetch --list``."""
    rows = []
    for name, spec in declared(path).items():
        executable = resolve_executable(name, path)
        rows.append(
            {
                "name": name,
                "description": spec.get("description", ""),
                "source": spec.get("source", "github-release"),
                "pinned": str(spec.get("tag", "")),
                "platform_supported": platform_key() in spec.get("platforms", {}),
                "executable": str(executable) if executable else None,
            }
        )
    return rows
