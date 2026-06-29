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
