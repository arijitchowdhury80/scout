#!/usr/bin/env python3
"""Smoke-test a published Scout Docker image.

Use this after Docker image publishing is explicitly approved and an image has
been pushed to a registry such as GHCR. The script pulls the image, runs it
locally, verifies public routes, and optionally runs authenticated `/scrape`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class DockerImageSmokeError(RuntimeError):
    """Raised when a published Docker image smoke fails."""


@dataclass(frozen=True)
class DockerImageSmokeResult:
    """Result of a Docker image smoke run."""

    image: str
    port: int
    scrape_checked: bool


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a command and raise with captured output on failure."""
    completed = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode != 0:
        raise DockerImageSmokeError(
            "Command failed: " + " ".join(command) + "\n" + completed.stdout[-4000:]
        )
    return completed


def wait_for_get(url: str, timeout_seconds: float = 45.0) -> str:
    """Wait for a public route to return a successful response."""
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=2.0) as response:
                body = response.read().decode("utf-8", errors="replace")
                if 200 <= response.status < 300:
                    return body
        except (HTTPError, URLError, OSError) as exc:
            last_error = str(exc)
        time.sleep(1)
    raise DockerImageSmokeError(f"Timed out waiting for {url}: {last_error}")


def post_json(url: str, payload: dict[str, object], headers: dict[str, str]) -> dict[str, object]:
    """POST JSON and return a JSON object."""
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60.0) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise DockerImageSmokeError(f"POST {url} failed with HTTP {exc.code}: {raw}") from exc
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise DockerImageSmokeError(f"POST {url} did not return a JSON object.")
    return parsed


def smoke_published_image(
    image: str,
    *,
    port: int = 18426,
    api_key: str = "dev-key",
    skip_pull: bool = False,
    skip_scrape: bool = False,
    scrape_url: str = "https://example.com",
) -> DockerImageSmokeResult:
    """Pull and smoke a published Scout Docker image."""
    if not skip_pull:
        run_command(["docker", "pull", image])
    container_id = ""
    try:
        completed = run_command(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "-p",
                f"{port}:8421",
                "-e",
                f"SCOUT_API_KEY={api_key}",
                "-e",
                "SCOUT_WORKDIR=/data/runs",
                "-e",
                "DB_PATH=/data/scout.db",
                image,
            ]
        )
        container_id = completed.stdout.strip()
        base_url = f"http://127.0.0.1:{port}"
        health = wait_for_get(f"{base_url}/health")
        if '"status":"ok"' not in health and '"status": "ok"' not in health:
            raise DockerImageSmokeError(f"Unexpected /health response: {health[:500]}")
        home = wait_for_get(f"{base_url}/")
        if "Scout" not in home:
            raise DockerImageSmokeError("Homepage did not contain Scout launch content.")
        styles = wait_for_get(f"{base_url}/styles.css")
        if "site-shell" not in styles:
            raise DockerImageSmokeError("Stylesheet did not contain expected website CSS.")
        if not skip_scrape:
            scrape = post_json(
                f"{base_url}/scrape",
                {"url": scrape_url},
                {"X-API-Key": api_key},
            )
            if scrape.get("success") is not True:
                raise DockerImageSmokeError(f"Authenticated scrape failed: {scrape}")
        return DockerImageSmokeResult(image=image, port=port, scrape_checked=not skip_scrape)
    finally:
        if container_id:
            run_command(["docker", "rm", "-f", container_id])


def build_parser() -> argparse.ArgumentParser:
    """Build CLI arguments."""
    parser = argparse.ArgumentParser(description="Smoke-test a published Scout Docker image.")
    parser.add_argument("image", help="Image reference, for example ghcr.io/org/scout:v0.1.0")
    parser.add_argument("--port", type=int, default=18426)
    parser.add_argument("--api-key", default="dev-key")
    parser.add_argument("--skip-pull", action="store_true")
    parser.add_argument("--skip-scrape", action="store_true")
    parser.add_argument("--scrape-url", default="https://example.com")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Docker image smoke."""
    args = build_parser().parse_args(argv)
    try:
        result = smoke_published_image(
            args.image,
            port=args.port,
            api_key=args.api_key,
            skip_pull=args.skip_pull,
            skip_scrape=args.skip_scrape,
            scrape_url=args.scrape_url,
        )
    except DockerImageSmokeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print("PASS: published Scout Docker image smoke-tested.")
    print(f"Image: {result.image}")
    print(f"Port: {result.port}")
    print(f"Authenticated scrape checked: {result.scrape_checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
