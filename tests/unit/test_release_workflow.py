from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _load_release_workflow() -> dict:
    workflow_path = ROOT / ".github" / "workflows" / "release.yml"
    with workflow_path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _all_run_commands(workflow: dict) -> str:
    commands: list[str] = []
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            if "run" in step:
                commands.append(step["run"])
    return "\n".join(commands)


def _all_uses(workflow: dict) -> str:
    uses: list[str] = []
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            if "uses" in step:
                uses.append(step["uses"])
    return "\n".join(uses)


def test_release_workflow_builds_and_smokes_tagged_artifacts() -> None:
    workflow = _load_release_workflow()
    workflow_on = workflow[True]
    commands = _all_run_commands(workflow)

    assert workflow_on["push"]["tags"] == ["v*"]
    assert "python -m build" in commands
    assert "python -m venv /tmp/scout-release-smoke" in commands
    assert "/tmp/scout-release-smoke/bin/python -m pip install dist/scout_web-*.whl" in commands
    assert "/tmp/scout-release-smoke/bin/python -c \"import scout; print('import-ok')\"" in commands
    assert "/tmp/scout-release-smoke/bin/scout --help" in commands


def test_release_workflow_smokes_docker_and_uploads_release_assets() -> None:
    workflow = _load_release_workflow()
    commands = _all_run_commands(workflow)
    uses = _all_uses(workflow)

    assert "docker build -f docker/Dockerfile -t scout:${{ github.ref_name }} ." in commands
    assert "docker run -d --rm -p 18422:8421" in commands
    assert "curl -fsS http://127.0.0.1:18422/health" in commands
    assert "curl -fsS http://127.0.0.1:18422/" in commands
    assert "curl -fsS http://127.0.0.1:18422/styles.css" in commands
    assert "softprops/action-gh-release" in uses
    assert "actions/upload-artifact" in uses


def test_release_workflow_remains_artifact_only_until_registry_policy_is_approved() -> None:
    workflow = _load_release_workflow()
    commands = _all_run_commands(workflow)
    uses = _all_uses(workflow)

    forbidden_commands = [
        "twine upload",
        "docker push",
        "docker login",
    ]
    forbidden_actions = [
        "pypa/gh-action-pypi-publish",
        "docker/login-action",
        "docker/build-push-action",
    ]

    for command in forbidden_commands:
        assert command not in commands
    for action in forbidden_actions:
        assert action not in uses


def test_release_artifact_smoke_helper_is_documented_for_downloaded_artifacts() -> None:
    helper = ROOT / "scripts" / "release_artifact_smoke.py"
    policy = (ROOT / "docs" / "product" / "registry-publishing-policy-2026-06-29.md").read_text(
        encoding="utf-8"
    )
    checklist = (ROOT / "docs" / "product" / "release-checklist.md").read_text(encoding="utf-8")

    assert helper.exists()
    assert "Smoke-test downloaded Scout GitHub Release artifacts" in helper.read_text(
        encoding="utf-8"
    )
    assert "scripts/release_artifact_smoke.py --dist-dir" in policy
    assert "/quickstart" in policy
    assert "Helper: `scripts/release_artifact_smoke.py`." in checklist
