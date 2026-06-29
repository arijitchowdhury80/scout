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


def _job(job_name: str) -> dict:
    return _ci()["jobs"][job_name]


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


def test_ci_runs_secret_scan_against_committed_baseline() -> None:
    runs = "\n".join(_step_runs("secret-scan"))

    assert "pip install detect-secrets" in runs
    assert "detect-secrets-hook --baseline .secrets.baseline" in runs
    assert "$(git ls-files)" in runs


def test_ci_lints_scripts_alongside_application_and_tests() -> None:
    runs = "\n".join(_step_runs("lint"))

    assert "ruff check scout/ tests/ scripts/" in runs
    assert "ruff format --check scout/ tests/ scripts/" in runs


def test_ci_runs_private_beta_launch_readiness_without_public_gate() -> None:
    job = _job("launch-readiness")
    runs = "\n".join(_step_runs("launch-readiness"))

    assert job["runs-on"] == "ubuntu-latest"
    assert "python scripts/launch_readiness_check.py" in runs
    assert "python scripts/launch_readiness_check.py --json" in runs
    assert "--require-public" not in runs


def test_ci_runs_dependency_audit_as_known_nonblocking_gate() -> None:
    job = _job("dependency-audit")
    runs = "\n".join(_step_runs("dependency-audit"))

    assert job["continue-on-error"] is True
    assert 'pip install ".[dev]"' in runs
    assert "pip install pip-audit" in runs
    assert "python -m pip_audit --local" in runs
