from __future__ import annotations

from pathlib import Path

import pytest

from scripts import release_artifact_smoke


def test_find_release_artifacts_requires_one_wheel_and_one_sdist(tmp_path: Path) -> None:
    wheel = tmp_path / "scout_web-0.1.0-py3-none-any.whl"
    sdist = tmp_path / "scout_web-0.1.0.tar.gz"
    wheel.write_text("wheel", encoding="utf-8")
    sdist.write_text("sdist", encoding="utf-8")

    assert release_artifact_smoke.find_release_artifacts(tmp_path) == (wheel, sdist)


def test_find_release_artifacts_fails_when_artifacts_are_missing(tmp_path: Path) -> None:
    with pytest.raises(release_artifact_smoke.ReleaseArtifactSmokeError, match="wheel"):
        release_artifact_smoke.find_release_artifacts(tmp_path)


def test_release_artifact_smoke_runs_expected_install_commands(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wheel = tmp_path / "scout_web-0.1.0-py3-none-any.whl"
    sdist = tmp_path / "scout_web-0.1.0.tar.gz"
    wheel.write_text("wheel", encoding="utf-8")
    sdist.write_text("sdist", encoding="utf-8")
    commands: list[list[str]] = []

    def fake_run_command(command: list[str], *, cwd: Path | None = None) -> object:
        del cwd
        commands.append(command)
        return object()

    monkeypatch.setattr(release_artifact_smoke, "run_command", fake_run_command)

    result = release_artifact_smoke.smoke_release_artifacts(tmp_path)

    assert result.wheel == wheel
    assert result.sdist == sdist
    assert result.serve_smoke is False
    assert any(command[-3:] == ["pip", "install", str(wheel)] for command in commands)
    assert any(command[-2:] == ["-c", "import scout; print('import-ok')"] for command in commands)
    assert any(command[-1:] == ["--help"] for command in commands)


def test_release_artifact_smoke_can_request_server_smoke(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "scout_web-0.1.0-py3-none-any.whl").write_text("wheel", encoding="utf-8")
    (tmp_path / "scout_web-0.1.0.tar.gz").write_text("sdist", encoding="utf-8")
    server_ports: list[int] = []

    monkeypatch.setattr(release_artifact_smoke, "run_command", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(
        release_artifact_smoke,
        "smoke_installed_server",
        lambda _scout, port: server_ports.append(port),
    )

    result = release_artifact_smoke.smoke_release_artifacts(tmp_path, serve=True, port=18455)

    assert result.serve_smoke is True
    assert server_ports == [18455]


def test_release_artifact_server_smoke_includes_launch_status_route() -> None:
    assert "/pricing" in release_artifact_smoke.public_server_smoke_routes()


def test_release_artifact_smoke_main_reports_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    wheel = tmp_path / "scout_web-0.1.0-py3-none-any.whl"
    sdist = tmp_path / "scout_web-0.1.0.tar.gz"
    monkeypatch.setattr(
        release_artifact_smoke,
        "smoke_release_artifacts",
        lambda *_args, **_kwargs: release_artifact_smoke.ReleaseArtifactSmokeResult(
            wheel=wheel,
            sdist=sdist,
            venv=tmp_path / "venv",
            serve_smoke=True,
        ),
    )

    assert release_artifact_smoke.main(["--dist-dir", str(tmp_path), "--serve"]) == 0

    output = capsys.readouterr().out
    assert "PASS" in output
    assert str(wheel) in output
    assert "Serve smoke: True" in output
