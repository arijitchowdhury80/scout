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
    assert report["public_launch"]["blocker_summary"] == {
        "total": 14,
        "by_type": {
            "engineering": 4,
            "external_smoke": 1,
            "founder_decision": 4,
            "legal_implementation": 4,
            "risk_decision": 1,
        },
    }
    assert report["public_launch"]["owner_summary"] == {
        "Arijit": 5,
        "Codex": 8,
        "Codex + Arijit": 1,
    }
    private_beta_areas = {check["area"] for check in report["private_beta"]["checks"]}
    assert len(report["private_beta"]["checks"]) >= 10
    assert "hosted operating contract" in private_beta_areas
    assert "scalability and security launch audit" in private_beta_areas
    assert "website hosted beta limits" in private_beta_areas
    assert all(check["status"] == "verified" for check in report["private_beta"]["checks"])

    blocker_areas = {blocker["area"] for blocker in report["public_launch"]["blockers"]}
    blocker_ids = [blocker["id"] for blocker in report["public_launch"]["blockers"]]
    assert "license decision" in blocker_areas
    assert "Stripe real test-mode smoke" in blocker_areas
    assert "Crawl4AI/lxml risk decision" in blocker_areas
    assert "pyproject license expression" in blocker_areas
    assert "LICENSE file" in blocker_areas
    assert len(blocker_ids) == len(set(blocker_ids))

    blockers_by_area = {blocker["area"]: blocker for blocker in report["public_launch"]["blockers"]}
    assert all("owner" in blocker for blocker in report["public_launch"]["blockers"])
    assert all("next_action" in blocker for blocker in report["public_launch"]["blockers"])
    assert all("closure_evidence" in blocker for blocker in report["public_launch"]["blockers"])
    assert all("codex_actionable_now" in blocker for blocker in report["public_launch"]["blockers"])
    assert blockers_by_area["license decision"]["blocker_type"] == "founder_decision"
    assert blockers_by_area["license decision"]["owner"] == "Arijit"
    assert blockers_by_area["license decision"]["codex_actionable_now"] is False
    assert blockers_by_area["final license expression"]["codex_actionable_now"] is False
    assert blockers_by_area["GitHub release workflow run"]["owner"] == "Codex"
    assert blockers_by_area["GitHub release workflow run"]["codex_actionable_now"] is False
    assert blockers_by_area["dependency audit blocking cleanly"]["owner"] == "Codex"
    assert blockers_by_area["Stripe real test-mode smoke"]["owner"] == "Codex + Arijit"
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
    assert payload["public_launch"]["blocker_summary"]["total"] == 14
    assert payload["public_launch"]["blocker_summary"]["by_type"]["founder_decision"] == 4
    assert payload["public_launch"]["owner_summary"]["Arijit"] == 5
    assert payload["public_launch"]["owner_summary"]["Codex"] == 8
    assert all("blocker_type" in blocker for blocker in payload["public_launch"]["blockers"])
    assert all("next_action" in blocker for blocker in payload["public_launch"]["blockers"])
    assert all("id" in blocker for blocker in payload["public_launch"]["blockers"])
    assert all("summary" in blocker for blocker in payload["public_launch"]["blockers"])

    blockers_by_area = {
        blocker["area"]: blocker for blocker in payload["public_launch"]["blockers"]
    }
    assert blockers_by_area["license decision"]["id"] == "license-decision"
    assert blockers_by_area["license decision"]["summary"] == "license decision"


def test_launch_readiness_json_can_filter_public_blockers_by_owner() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--json", "--owner", "arijit"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["private_beta"]["status"] == "ready_with_limits"
    assert payload["public_launch"]["status"] == "blocked"
    assert payload["public_launch"]["blocker_summary"] == {
        "total": 5,
        "by_type": {
            "founder_decision": 4,
            "risk_decision": 1,
        },
    }
    assert payload["public_launch"]["owner_summary"] == {"Arijit": 5}
    assert {blocker["owner"] for blocker in payload["public_launch"]["blockers"]} == {"Arijit"}
    assert "license decision" in {
        blocker["area"] for blocker in payload["public_launch"]["blockers"]
    }
    assert "GitHub release workflow run" not in {
        blocker["area"] for blocker in payload["public_launch"]["blockers"]
    }


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

    assert "Public launch: blocked" in result.stdout
    assert "Blocker summary: 4 total" in result.stdout
    assert "founder_decision: 4" in result.stdout
    assert "license-decision: license decision [founder_decision]" in result.stdout
    assert (
        "github-release-workflow-run: GitHub release workflow run [engineering]"
        not in result.stdout
    )
    assert (
        "crawl4ai-lxml-risk-decision: Crawl4AI/lxml risk decision [risk_decision]"
        not in result.stdout
    )


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
    assert "Blocker summary: 14 total" in result.stdout
    assert "Owner summary:" in result.stdout
    assert "Arijit: 5" in result.stdout
    assert "Codex: 8" in result.stdout
    assert "founder_decision: 4" in result.stdout
    assert "license-decision: license decision [founder_decision]" in result.stdout
    assert "owner: Arijit" in result.stdout
    assert "next action: Approve Apache-2.0 for Scout local/core" in result.stdout
    assert (
        "closure evidence: Signed founder decision record plus updated release checklist."
        in result.stdout
    )
    assert "codex actionable now: false" in result.stdout
    assert "owner: Codex + Arijit" in result.stdout
    assert "next action: Configure Stripe test keys/webhook secret" in result.stdout
