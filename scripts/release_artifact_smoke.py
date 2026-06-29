#!/usr/bin/env python3
"""Smoke-test downloaded Scout GitHub Release artifacts.

Use this after an approved `v*` release tag has produced wheel/sdist files and
the artifacts have been downloaded locally. The script installs the wheel into
a fresh virtual environment, imports Scout, runs `scout --help`, and optionally
starts `scout serve` to verify public website routes.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


class ReleaseArtifactSmokeError(RuntimeError):
    """Raised when downloaded release artifacts fail smoke verification."""


@dataclass(frozen=True)
class ReleaseArtifactSmokeResult:
    """Result of a release artifact smoke run."""

    wheel: Path
    sdist: Path
    venv: Path
    serve_smoke: bool


def find_release_artifacts(dist_dir: Path) -> tuple[Path, Path]:
    """Return the single Scout wheel and sdist from a downloaded artifact dir."""
    if not dist_dir.exists():
        raise ReleaseArtifactSmokeError(f"Artifact directory does not exist: {dist_dir}")
    wheels = sorted(dist_dir.glob("scout_web-*.whl"))
    sdists = sorted(dist_dir.glob("scout_web-*.tar.gz"))
    if len(wheels) != 1:
        raise ReleaseArtifactSmokeError(
            f"Expected exactly one scout_web wheel in {dist_dir}, found {len(wheels)}."
        )
    if len(sdists) != 1:
        raise ReleaseArtifactSmokeError(
            f"Expected exactly one scout_web sdist in {dist_dir}, found {len(sdists)}."
        )
    return wheels[0], sdists[0]


def run_command(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and raise with captured output on failure."""
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise ReleaseArtifactSmokeError(
            "Command failed: " + " ".join(command) + "\n" + completed.stdout[-4000:]
        )
    return completed


def smoke_release_artifacts(
    dist_dir: Path,
    *,
    keep_venv: bool = False,
    serve: bool = False,
    port: int = 18424,
) -> ReleaseArtifactSmokeResult:
    """Smoke-test downloaded release artifacts in a fresh virtual environment."""
    wheel, sdist = find_release_artifacts(dist_dir)
    venv = Path(tempfile.mkdtemp(prefix="scout-release-artifact-smoke-"))
    try:
        run_command([sys.executable, "-m", "venv", str(venv)])
        python = venv / "bin" / "python"
        scout = venv / "bin" / "scout"
        run_command([str(python), "-m", "pip", "install", "--upgrade", "pip"])
        run_command([str(python), "-m", "pip", "install", str(wheel)])
        run_command([str(python), "-c", "import scout; print('import-ok')"])
        run_command([str(scout), "--help"])
        if serve:
            smoke_installed_server(scout, port)
        return ReleaseArtifactSmokeResult(wheel=wheel, sdist=sdist, venv=venv, serve_smoke=serve)
    except Exception:
        if not keep_venv:
            shutil.rmtree(venv, ignore_errors=True)
        raise
    finally:
        if not keep_venv:
            shutil.rmtree(venv, ignore_errors=True)


def smoke_installed_server(scout: Path, port: int) -> None:
    """Start installed Scout briefly and verify public routes."""
    process = subprocess.Popen(
        [
            str(scout),
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={
            **os.environ,
            "SCOUT_API_KEY": "dev-key",
            "SCOUT_WORKDIR": tempfile.mkdtemp(prefix="scout-release-server-runs-"),
        },
    )
    try:
        base = f"http://127.0.0.1:{port}"
        wait_for_route(f"{base}/health")
        for route in public_server_smoke_routes():
            wait_for_route(f"{base}{route}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def public_server_smoke_routes() -> list[str]:
    """Return public routes that release artifact server smoke must verify."""
    return ["/", "/styles.css", "/quickstart", "/status"]


def wait_for_route(url: str, timeout_seconds: float = 30.0) -> None:
    """Wait until a URL returns a successful response."""
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2.0) as response:
                if 200 <= response.status < 300:
                    return
        except URLError as exc:
            last_error = str(exc)
        time.sleep(1)
    raise ReleaseArtifactSmokeError(f"Timed out waiting for {url}: {last_error}")


def build_parser() -> argparse.ArgumentParser:
    """Build CLI arguments."""
    parser = argparse.ArgumentParser(description="Smoke downloaded Scout release artifacts.")
    parser.add_argument("--dist-dir", type=Path, default=Path("dist"))
    parser.add_argument("--keep-venv", action="store_true")
    parser.add_argument("--serve", action="store_true", help="Also smoke installed scout serve.")
    parser.add_argument("--port", type=int, default=18424)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the release artifact smoke."""
    args = build_parser().parse_args(argv)
    try:
        result = smoke_release_artifacts(
            args.dist_dir,
            keep_venv=args.keep_venv,
            serve=args.serve,
            port=args.port,
        )
    except ReleaseArtifactSmokeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print("PASS: downloaded Scout release artifacts smoke-tested.")
    print(f"Wheel: {result.wheel}")
    print(f"Sdist: {result.sdist}")
    print(f"Serve smoke: {result.serve_smoke}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
