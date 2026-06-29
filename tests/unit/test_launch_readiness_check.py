from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scout.launch_readiness import build_report


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "launch_readiness_check.py"


def test_launch_readiness_report_marks_private_beta_ready_and_public_blocked() -> None:
    report = build_report(ROOT)

    assert report["private_beta"]["status"] == "ready_with_limits"
    assert report["public_launch"]["status"] == "blocked"
    private_beta_areas = {check["area"] for check in report["private_beta"]["checks"]}
    assert len(report["private_beta"]["checks"]) >= 9
    assert "hosted operating contract" in private_beta_areas
    assert "scalability and security launch audit" in private_beta_areas
    assert all(check["status"] == "verified" for check in report["private_beta"]["checks"])

    blocker_areas = {blocker["area"] for blocker in report["public_launch"]["blockers"]}
    assert "license decision" in blocker_areas
    assert "Stripe real test-mode smoke" in blocker_areas
    assert "Crawl4AI/lxml risk decision" in blocker_areas
    assert "pyproject license expression" in blocker_areas
    assert "LICENSE file" in blocker_areas

    blockers_by_area = {blocker["area"]: blocker for blocker in report["public_launch"]["blockers"]}
    assert blockers_by_area["license decision"]["blocker_type"] == "founder_decision"
    assert (
        blockers_by_area["public pricing and hosted usage limits"]["blocker_type"]
        == "founder_decision"
    )
    assert blockers_by_area["GitHub release workflow run"]["blocker_type"] == "engineering"
    assert blockers_by_area["Stripe real test-mode smoke"]["blocker_type"] == "external_smoke"
    assert blockers_by_area["Crawl4AI/lxml risk decision"]["blocker_type"] == "risk_decision"
    assert (
        blockers_by_area["pyproject license expression"]["blocker_type"] == "legal_implementation"
    )


def test_launch_readiness_script_outputs_json() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["private_beta"]["status"] == "ready_with_limits"
    assert payload["public_launch"]["status"] == "blocked"
    assert all("blocker_type" in blocker for blocker in payload["public_launch"]["blockers"])


def test_launch_readiness_script_can_fail_for_public_launch_gate() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--require-public"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Private beta: ready_with_limits" in result.stdout
    assert "Public launch: blocked" in result.stdout
    assert "license decision [founder_decision]" in result.stdout
