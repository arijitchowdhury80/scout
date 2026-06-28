"""Tests for GitHub CI gates that protect launch distribution paths."""

from __future__ import annotations

from pathlib import Path

import yaml


_CI_WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def _ci() -> dict:
    return yaml.safe_load(_CI_WORKFLOW.read_text(encoding="utf-8"))


def _step_runs(job_name: str) -> list[str]:
    return [
        step["run"]
        for step in _ci()["jobs"][job_name]["steps"]
        if isinstance(step, dict) and "run" in step
    ]


def test_ci_builds_wheel_and_smokes_installed_cli() -> None:
    runs = "\n".join(_step_runs("package-build"))

    assert "python -m build" in runs
    assert "pip install dist/scout_web-0.1.0-py3-none-any.whl" in runs
    assert "scout --help" in runs
    assert "python -c \"import scout; print('import-ok')\"" in runs


def test_ci_docker_job_smokes_built_container_routes() -> None:
    runs = "\n".join(_step_runs("docker-build"))

    assert "docker build -f docker/Dockerfile -t scout:ci ." in runs
    assert "docker run -d --rm -p 18421:8421" in runs
    assert "curl -fsS http://127.0.0.1:18421/health" in runs
    assert "curl -fsS http://127.0.0.1:18421/" in runs
    assert "curl -fsS http://127.0.0.1:18421/styles.css" in runs
