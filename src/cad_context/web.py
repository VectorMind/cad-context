"""Starting the preview web app.

The web app under ``webapp/`` is an Astro SSR server whose handlers shell out
to this CLI. There is no second long-running Python process: the "backend" of a
page is ``uv run cadctx generate …``, spawned per request. Starting the whole
thing is therefore one command — this module is what ``cadctx web`` runs.

Console discipline still applies: the dev server's own output is streamed into
``.cache/reports/web.log`` and referenced by path, never echoed.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from . import workspace

WEBAPP_DIRNAME = "webapp"
READY_PATTERN = re.compile(r"https?://(?:localhost|127\.0\.0\.1):(\d+)")
READY_TIMEOUT_S = 120.0


class WebAppError(RuntimeError):
    """The web app could not be started; the message says what to fix."""


@dataclass
class DevServer:
    process: subprocess.Popen[bytes]
    url: str
    log: Path

    def wait(self) -> int:
        """Block until the server exits (Ctrl-C included)."""
        try:
            return self.process.wait()
        except KeyboardInterrupt:
            self.stop()
            return 0

    def stop(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:  # pragma: no cover - last resort
                self.process.kill()


def webapp_dir() -> Path:
    directory = workspace.repo_root() / WEBAPP_DIRNAME
    if not (directory / "package.json").exists():
        raise WebAppError(f"no web app at {workspace.rel(directory)}")
    return directory


def package_manager() -> tuple[str, ...]:
    pnpm = shutil.which("pnpm")
    if pnpm:
        return (pnpm,)
    corepack = shutil.which("corepack")
    if corepack:
        return (corepack, "pnpm")
    raise WebAppError(
        "pnpm/corepack was not found on PATH — install Node.js 22+ and re-run"
    )


def dependencies_installed(directory: Path) -> bool:
    return (directory / "node_modules" / "astro").exists()


def install(directory: Path, log: Path) -> None:
    """Run ``pnpm install`` with its output parked in the report log."""
    with log.open("a", encoding="utf-8") as handle:
        handle.write("$ pnpm install\n")
        handle.flush()
        completed = subprocess.run(
            [*package_manager(), "install"],
            cwd=directory,
            stdout=handle,
            stderr=subprocess.STDOUT,
            check=False,
        )
    if completed.returncode != 0:
        raise WebAppError(f"pnpm install failed — see {workspace.rel(log)}")


def start(
    directory: Path,
    log: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 4321,
    timeout: float = READY_TIMEOUT_S,
    project: Path | None = None,
) -> DevServer:
    """Spawn ``pnpm dev`` and return once it answers HTTP (or fail loudly)."""
    log.parent.mkdir(parents=True, exist_ok=True)
    handle = log.open("w", encoding="utf-8")
    handle.write(f"$ pnpm dev --host {host} --port {port}\n")
    handle.flush()
    environment = os.environ.copy()
    if project is None:
        environment.pop("CAD_CONTEXT_PROJECT", None)
        environment["CAD_CONTEXT_NO_PROJECT"] = "1"
    else:
        environment["CAD_CONTEXT_PROJECT"] = str(project)
        environment.pop("CAD_CONTEXT_NO_PROJECT", None)
    process = subprocess.Popen(  # noqa: S603 - fixed argv, no shell
        [*package_manager(), "dev", "--host", host, "--port", str(port)],
        cwd=directory,
        stdout=handle,
        stderr=subprocess.STDOUT,
        env=environment,
    )
    handle.close()  # the child holds its own duplicate of the descriptor
    try:
        url = _wait_until_ready(process, log, host, port, timeout)
    except Exception:
        process.terminate()
        raise
    return DevServer(process=process, url=url, log=log)


def _wait_until_ready(
    process: subprocess.Popen[bytes],
    log: Path,
    host: str,
    port: int,
    timeout: float,
) -> str:
    """Read the port the dev server actually bound, then prove it answers.

    Astro moves to the next free port when one is taken, so the announced URL
    is read back from its output instead of being assumed.
    """
    deadline = time.monotonic() + timeout
    bound_port: int | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise WebAppError(
                f"the dev server exited with code {process.returncode} — "
                f"see {workspace.rel(log)}"
            )
        if bound_port is None:
            text = log.read_text(encoding="utf-8", errors="replace")
            match = READY_PATTERN.search(text)
            if match:
                bound_port = int(match.group(1))
        if bound_port is not None:
            url = f"http://{host}:{bound_port}/"
            if _responds(url):
                return url
        time.sleep(0.25)
    raise WebAppError(
        f"the dev server did not answer within {timeout:.0f}s — "
        f"see {workspace.rel(log)}"
    )


def _responds(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2) as response:  # noqa: S310
            return response.status < 500
    except (urllib.error.URLError, OSError):
        return False
