from __future__ import annotations

from dataclasses import dataclass

from scripts import docker_image_smoke


@dataclass
class FakeCompleted:
    stdout: str = ""
    returncode: int = 0


def test_docker_image_smoke_pulls_runs_routes_scrapes_and_cleans_up(
    monkeypatch,
) -> None:
    commands: list[list[str]] = []
    gets: list[str] = []
    posts: list[tuple[str, dict[str, object], dict[str, str]]] = []

    def fake_run_command(command: list[str]) -> FakeCompleted:
        commands.append(command)
        if command[:3] == ["docker", "run", "-d"]:
            return FakeCompleted(stdout="container-123\n")
        return FakeCompleted()

    def fake_wait_for_get(url: str, timeout_seconds: float = 45.0) -> str:
        del timeout_seconds
        gets.append(url)
        if url.endswith("/health"):
            return '{"status":"ok"}'
        if url.endswith("/styles.css"):
            return ".site-shell {}"
        return "Scout launch website"

    def fake_post_json(
        url: str,
        payload: dict[str, object],
        headers: dict[str, str],
    ) -> dict[str, object]:
        posts.append((url, payload, headers))
        return {"success": True}

    monkeypatch.setattr(docker_image_smoke, "run_command", fake_run_command)
    monkeypatch.setattr(docker_image_smoke, "wait_for_get", fake_wait_for_get)
    monkeypatch.setattr(docker_image_smoke, "post_json", fake_post_json)

    result = docker_image_smoke.smoke_published_image(
        "ghcr.io/example/scout:v0.1.0",
        port=18499,
        api_key="test-key",
    )

    assert result.image == "ghcr.io/example/scout:v0.1.0"
    assert result.port == 18499
    assert result.scrape_checked is True
    assert ["docker", "pull", "ghcr.io/example/scout:v0.1.0"] in commands
    assert any(command[:4] == ["docker", "run", "-d", "--rm"] for command in commands)
    assert ["docker", "rm", "-f", "container-123"] in commands
    assert "http://127.0.0.1:18499/health" in gets
    assert "http://127.0.0.1:18499/" in gets
    assert "http://127.0.0.1:18499/styles.css" in gets
    assert posts == [
        (
            "http://127.0.0.1:18499/scrape",
            {"url": "https://example.com"},
            {"X-API-Key": "test-key"},
        )
    ]


def test_docker_image_smoke_can_skip_pull_and_scrape(monkeypatch) -> None:
    commands: list[list[str]] = []

    def fake_run_command(command: list[str]) -> FakeCompleted:
        commands.append(command)
        if command[:3] == ["docker", "run", "-d"]:
            return FakeCompleted(stdout="container-123\n")
        return FakeCompleted()

    monkeypatch.setattr(docker_image_smoke, "run_command", fake_run_command)
    monkeypatch.setattr(
        docker_image_smoke,
        "wait_for_get",
        lambda url, timeout_seconds=45.0: (
            '{"status":"ok"}'
            if url.endswith("/health")
            else ".site-shell {}"
            if url.endswith("/styles.css")
            else "Scout"
        ),
    )

    result = docker_image_smoke.smoke_published_image(
        "scout:local",
        skip_pull=True,
        skip_scrape=True,
    )

    assert result.scrape_checked is False
    assert ["docker", "pull", "scout:local"] not in commands


def test_docker_image_smoke_main_reports_success(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        docker_image_smoke,
        "smoke_published_image",
        lambda *_args, **_kwargs: docker_image_smoke.DockerImageSmokeResult(
            image="ghcr.io/example/scout:v0.1.0",
            port=18426,
            scrape_checked=True,
        ),
    )

    assert docker_image_smoke.main(["ghcr.io/example/scout:v0.1.0"]) == 0

    output = capsys.readouterr().out
    assert "PASS" in output
    assert "ghcr.io/example/scout:v0.1.0" in output
    assert "Authenticated scrape checked: True" in output
