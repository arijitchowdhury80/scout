from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scout.launch_readiness import build_report


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "launch_readiness_check.py"


def test_launch_readiness_report_marks_current_release_ready() -> None:
    report = build_report(ROOT)

    assert report["private_beta"]["status"] == "ready_with_limits"
    assert report["public_launch"]["status"] == "ready"
    assert report["public_launch"]["blocker_summary"] == {
        "total": 0,
        "by_type": {},
    }
    assert report["public_launch"]["owner_summary"] == {}
    assert report["public_launch"]["actionable_summary"] == {
        "codex_actionable_now": 0,
    }
    private_beta_areas = {check["area"] for check in report["private_beta"]["checks"]}
    assert len(report["private_beta"]["checks"]) >= 10
    assert "hosted operating contract" in private_beta_areas
    assert "scalability and security launch audit" in private_beta_areas
    assert "website hosted pricing posture" in private_beta_areas
    assert all(check["status"] == "verified" for check in report["private_beta"]["checks"])

    assert report["public_launch"]["blockers"] == []


def test_launch_readiness_script_outputs_json() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["private_beta"]["status"] == "ready_with_limits"
    assert payload["public_launch"]["status"] == "ready"
    assert payload["public_launch"]["blocker_summary"]["total"] == 0
    assert payload["public_launch"]["blocker_summary"]["by_type"] == {}
    assert payload["public_launch"]["owner_summary"] == {}
    assert payload["public_launch"]["actionable_summary"]["codex_actionable_now"] == 0
    assert payload["public_launch"]["blockers"] == []


def test_launch_readiness_json_can_filter_public_blockers_by_owner() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--json", "--owner", "arijit"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["private_beta"]["status"] == "ready_with_limits"
    assert payload["public_launch"]["status"] == "ready"
    assert payload["public_launch"]["blocker_summary"] == {
        "total": 0,
        "by_type": {},
    }
    assert payload["public_launch"]["owner_summary"] == {}
    assert payload["public_launch"]["blockers"] == []


def test_launch_readiness_json_can_filter_public_blockers_by_id() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(ROOT),
            "--json",
            "--blocker-id",
            "public-pricing-and-hosted-usage-limits",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["private_beta"]["status"] == "ready_with_limits"
    assert payload["public_launch"]["status"] == "ready"
    assert payload["public_launch"]["blocker_summary"] == {
        "total": 0,
        "by_type": {},
    }
    assert payload["public_launch"]["owner_summary"] == {}
    assert payload["public_launch"]["blockers"] == []


def test_launch_readiness_text_can_filter_public_blockers_by_type() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(ROOT),
            "--blocker-type",
            "founder_decision",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Public launch: ready" in result.stdout
    assert "Blocker summary: 0 total" in result.stdout
    assert "founder_decision: 3" not in result.stdout
    assert "public-pricing-and-hosted-usage-limits" not in result.stdout
    assert "license-decision: license decision [founder_decision]" not in result.stdout
    assert (
        "github-release-workflow-run: GitHub release workflow run [engineering]"
        not in result.stdout
    )
    assert (
        "crawl4ai-lxml-risk-decision: Crawl4AI/lxml risk decision [risk_decision]"
        not in result.stdout
    )


def test_launch_readiness_text_can_filter_similar_public_blockers_by_exact_id() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(ROOT),
            "--blocker-id",
            "published-docker-image-smoke",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Public launch: ready" in result.stdout
    assert "Blocker summary: 0 total" in result.stdout
    assert "engineering: 1" not in result.stdout
    assert "published-docker-image-smoke" not in result.stdout
    assert (
        "docker-image-publishing-policy: Docker image publishing policy [founder_decision]"
        not in result.stdout
    )


def test_launch_readiness_script_can_fail_for_public_launch_gate() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--require-public"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Private beta: ready_with_limits" in result.stdout
    assert "Public launch: ready" in result.stdout
    assert "Blocker summary: 0 total" in result.stdout
    assert "Codex actionable now: 0" in result.stdout
    assert "Owner summary:" not in result.stdout
    assert "Arijit: 4" not in result.stdout
    assert "Codex: 4" not in result.stdout
    assert "founder_decision: 3" not in result.stdout
    assert "license-decision: license decision [founder_decision]" not in result.stdout
    assert "owner: Arijit" not in result.stdout
    assert "codex actionable now: false" not in result.stdout
