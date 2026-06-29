"""Scout private-beta and public-launch readiness checks."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from scout.core.platform.hosted import HostedPlan, plan_limits


@dataclass(frozen=True)
class EvidenceCheck:
    area: str
    status: str
    evidence: str
    note: str
    blocker_type: str = "evidence"
    owner: str = ""
    next_action: str = ""
    closure_evidence: str = ""
    codex_actionable_now: bool | None = None

    def as_dict(self) -> dict[str, str | bool]:
        payload: dict[str, str | bool] = {
            "id": _stable_id(self.area),
            "area": self.area,
            "summary": self.area,
            "status": self.status,
            "evidence": self.evidence,
            "note": self.note,
            "blocker_type": self.blocker_type,
        }
        if self.owner:
            payload["owner"] = self.owner
        if self.next_action:
            payload["next_action"] = self.next_action
        if self.closure_evidence:
            payload["closure_evidence"] = self.closure_evidence
        if self.codex_actionable_now is not None:
            payload["codex_actionable_now"] = self.codex_actionable_now
        return payload


def _stable_id(value: str) -> str:
    """Return a stable, readable identifier for readiness checks."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "check"


PRIVATE_BETA_EVIDENCE = [
    (
        "launch website",
        "docs/product/website-route-render-verification-2026-06-29.md",
        "Launch website route/render smoke passed locally",
    ),
    (
        "local install",
        "docs/product/local-install-verification-2026-06-28.md",
        "Private-beta branch install path verified",
    ),
    (
        "Docker from source",
        "docs/product/docker-install-verification-2026-06-28.md",
        "Status: passed",
    ),
    (
        "hosted API quickstart",
        "docs/product/hosted-api-quickstart-verification-2026-06-28.md",
        "freshly generated hosted beta key",
    ),
    (
        "hosted operating contract",
        "docs/product/hosted-operating-contract-2026-06-29.md",
        "Private-beta hosted operating contract",
    ),
    (
        "scalability and security launch audit",
        "docs/product/scalability-security-audit-2026-06-29.md",
        "Private-beta scale/security audit",
    ),
    (
        "skill usage",
        "docs/product/skill-usage-verification-2026-06-29.md",
        "skill CLI examples",
    ),
    (
        "product exports",
        "docs/product/product-export-generalization-verification-2026-06-29.md",
        "Verified for private beta",
    ),
    (
        "beta onboarding",
        "docs/product/private-beta-onboarding-and-support.md",
        "Private Beta Onboarding And Support",
    ),
]


PUBLIC_BLOCKER_LINES = [
    ("license decision", "founder_decision", "- [ ] License decision recorded."),
    (
        "final license expression",
        "legal_implementation",
        "- [ ] Final license expression added to `pyproject.toml`.",
    ),
    (
        "LICENSE file",
        "legal_implementation",
        "- [ ] `LICENSE` file added if Scout is open source or source-available.",
    ),
    (
        "public pricing and hosted usage limits",
        "founder_decision",
        "- [ ] Public launch pricing and hosted usage limits approved.",
    ),
    (
        "registry publishing policy",
        "founder_decision",
        "- [ ] Registry publishing policy approved for PyPI, GHCR, Docker Hub, or other",
    ),
    (
        "GitHub release workflow run",
        "engineering",
        "- [ ] GitHub release artifact workflow run against a real `v*` tag.",
    ),
    (
        "release artifact smoke",
        "engineering",
        "- [ ] Release artifact downloaded from GitHub Release and smoke-tested locally.",
    ),
    (
        "Docker image publishing policy",
        "founder_decision",
        "- [ ] Docker image publishing policy approved.",
    ),
    (
        "published Docker image smoke",
        "engineering",
        "- [ ] Published Docker image smoke-tested if GHCR, Docker Hub, or another",
    ),
    (
        "Crawl4AI/lxml risk decision",
        "risk_decision",
        "- [ ] Crawl4AI/lxml risk decision approved.",
    ),
    (
        "dependency audit blocking cleanly",
        "engineering",
        "- [ ] Dependency audit clean and blocking in GitHub CI.",
    ),
    (
        "Stripe real test-mode smoke",
        "external_smoke",
        "- [ ] Stripe checkout and webhook tested in Stripe test mode.",
    ),
]


PUBLIC_BLOCKER_REMEDIATION = {
    "license decision": {
        "owner": "Arijit",
        "next_action": "Approve Apache-2.0 for Scout local/core or choose another license path.",
        "closure_evidence": "Signed founder decision record plus updated release checklist.",
        "codex_actionable_now": False,
    },
    "final license expression": {
        "owner": "Codex",
        "next_action": "Add the approved SPDX license expression to pyproject.toml after license approval.",
        "closure_evidence": "pyproject.toml contains the approved license expression and package metadata tests pass.",
        "codex_actionable_now": False,
    },
    "LICENSE file": {
        "owner": "Codex",
        "next_action": "Add the approved LICENSE file after license approval.",
        "closure_evidence": "LICENSE exists and wheel/sdist include license and third-party notices.",
        "codex_actionable_now": False,
    },
    "public pricing and hosted usage limits": {
        "owner": "Arijit",
        "next_action": "Approve public pricing or explicitly keep only the finite private-beta pass.",
        "closure_evidence": "Founder decision record and website/pricing docs updated to match the approved policy.",
        "codex_actionable_now": False,
    },
    "registry publishing policy": {
        "owner": "Arijit",
        "next_action": "Approve artifact-only beta tags, PyPI, GHCR, Docker Hub, or another publishing path.",
        "closure_evidence": "Founder decision record and release checklist publishing gates updated.",
        "codex_actionable_now": False,
    },
    "GitHub release workflow run": {
        "owner": "Codex",
        "next_action": "After approval and license implementation, push an approved v* tag and record the workflow URL.",
        "closure_evidence": "GitHub release workflow URL and successful run summary.",
        "codex_actionable_now": False,
    },
    "release artifact smoke": {
        "owner": "Codex",
        "next_action": "Download release artifacts from the approved tag and run scripts/release_artifact_smoke.py.",
        "closure_evidence": "Smoke output proving installed release artifacts serve /health, website routes, and CLI help.",
        "codex_actionable_now": False,
    },
    "Docker image publishing policy": {
        "owner": "Arijit",
        "next_action": "Approve or defer GHCR/Docker Hub publishing.",
        "closure_evidence": "Founder decision record and release checklist Docker publishing gate updated.",
        "codex_actionable_now": False,
    },
    "published Docker image smoke": {
        "owner": "Codex",
        "next_action": "After image publishing approval, pull the published image and run scripts/docker_image_smoke.py.",
        "closure_evidence": "Fresh published image smoke output for /health, website, and authenticated scrape.",
        "codex_actionable_now": False,
    },
    "Crawl4AI/lxml risk decision": {
        "owner": "Arijit",
        "next_action": "Accept a formal private-beta exception, wait for a clean upstream path, or approve dependency replacement.",
        "closure_evidence": "Risk decision packet signed and dependency audit posture reflected in release checklist.",
        "codex_actionable_now": False,
    },
    "dependency audit blocking cleanly": {
        "owner": "Codex",
        "next_action": "Make CI dependency audit blocking after the clean dependency path or formal exception is approved.",
        "closure_evidence": "GitHub CI dependency audit is blocking and passes, or blocks with an approved exception gate.",
        "codex_actionable_now": False,
    },
    "Stripe real test-mode smoke": {
        "owner": "Codex + Arijit",
        "next_action": "Configure Stripe test keys/webhook secret, complete a test checkout, deliver webhook, and verify hosted key access.",
        "closure_evidence": "Stripe test-mode smoke report with checkout, webhook, hosted key delivery, and /v1/hosted/me verification.",
        "codex_actionable_now": False,
    },
    "pyproject license expression": {
        "owner": "Codex",
        "next_action": "Add approved license expression to pyproject.toml after founder/legal approval.",
        "closure_evidence": "pyproject.toml contains final approved license expression and metadata tests pass.",
        "codex_actionable_now": False,
    },
}


def default_root() -> Path:
    """Return the best root containing Scout launch evidence."""
    package_root = Path(__file__).resolve().parents[1]
    for candidate in (Path.cwd(), package_root):
        if (candidate / "docs/product/release-checklist.md").exists():
            return candidate.resolve()
    return Path.cwd().resolve()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _evidence_status(root: Path, path_text: str, marker: str) -> EvidenceCheck:
    path = root / path_text
    if not path.exists():
        return EvidenceCheck(
            area=path_text,
            status="missing",
            evidence=path_text,
            note="Evidence file is missing.",
        )

    content = _read(path)
    if marker not in content:
        return EvidenceCheck(
            area=path_text,
            status="weak",
            evidence=path_text,
            note=f"Evidence file exists but marker is absent: {marker}",
        )

    return EvidenceCheck(
        area=path_text,
        status="verified",
        evidence=path_text,
        note="Evidence marker found.",
    )


def _private_beta_checks(root: Path) -> list[EvidenceCheck]:
    checks: list[EvidenceCheck] = []
    for area, path_text, marker in PRIVATE_BETA_EVIDENCE:
        check = _evidence_status(root, path_text, marker)
        checks.append(
            EvidenceCheck(
                area=area,
                status=check.status,
                evidence=check.evidence,
                note=check.note,
            )
        )
    checks.append(_website_hosted_beta_limits_status(root))
    return checks


def _website_hosted_beta_limits_status(root: Path) -> EvidenceCheck:
    """Verify website pages expose the code-aligned hosted beta limits."""
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)
    required_markers = [
        f"{limits.standard_credits:,} standard credits",
        f"{limits.browser_credits:,} browser credits",
        f"{limits.artifact_retention_days}-day artifact retention",
        f"{limits.max_pages_per_run:,} pages per run",
    ]
    website_pages = [
        "website/pricing.html",
        "website/beta.html",
        "website/quickstart.html",
    ]

    missing_pages = [page for page in website_pages if not (root / page).exists()]
    if missing_pages:
        return EvidenceCheck(
            area="website hosted beta limits",
            status="missing",
            evidence=", ".join(missing_pages),
            note="Website page is missing.",
        )

    missing_markers: list[str] = []
    for page in website_pages:
        content = " ".join(_read(root / page).split())
        for marker in required_markers:
            if marker not in content:
                missing_markers.append(f"{page}: {marker}")

    if missing_markers:
        return EvidenceCheck(
            area="website hosted beta limits",
            status="weak",
            evidence=", ".join(website_pages),
            note="Missing hosted beta limit markers: " + "; ".join(missing_markers),
        )

    return EvidenceCheck(
        area="website hosted beta limits",
        status="verified",
        evidence=", ".join(website_pages),
        note="Website exposes code-aligned hosted beta pass limits.",
    )


def _with_remediation(check: EvidenceCheck) -> EvidenceCheck:
    """Attach public-launch remediation metadata when known."""
    remediation = PUBLIC_BLOCKER_REMEDIATION.get(check.area, {})
    return EvidenceCheck(
        area=check.area,
        status=check.status,
        evidence=check.evidence,
        note=check.note,
        blocker_type=check.blocker_type,
        owner=str(remediation.get("owner", "")),
        next_action=str(remediation.get("next_action", "")),
        closure_evidence=str(remediation.get("closure_evidence", "")),
        codex_actionable_now=remediation.get("codex_actionable_now"),
    )


def _public_blockers(root: Path) -> list[EvidenceCheck]:
    checklist_path = root / "docs/product/release-checklist.md"
    if not checklist_path.exists():
        return [
            EvidenceCheck(
                area="release checklist",
                status="blocked",
                evidence="docs/product/release-checklist.md",
                note="Release checklist is missing.",
            )
        ]

    checklist = _read(checklist_path)
    blockers: list[EvidenceCheck] = []
    for area, blocker_type, marker in PUBLIC_BLOCKER_LINES:
        if marker in checklist:
            blockers.append(
                _with_remediation(
                    EvidenceCheck(
                        area=area,
                        status="blocked",
                        evidence="docs/product/release-checklist.md",
                        note=f"Unchecked gate remains: {marker}",
                        blocker_type=blocker_type,
                    )
                )
            )

    pyproject = _read(root / "pyproject.toml") if (root / "pyproject.toml").exists() else ""
    if 'license = "' not in pyproject:
        blockers.append(
            _with_remediation(
                EvidenceCheck(
                    area="pyproject license expression",
                    status="blocked",
                    evidence="pyproject.toml",
                    note="No final project license expression is present.",
                    blocker_type="legal_implementation",
                )
            )
        )

    if not (root / "LICENSE").exists():
        blockers.append(
            _with_remediation(
                EvidenceCheck(
                    area="LICENSE file",
                    status="blocked",
                    evidence="LICENSE",
                    note="No project LICENSE file is present.",
                    blocker_type="legal_implementation",
                )
            )
        )

    return blockers


def _blocker_summary(blockers: list[EvidenceCheck]) -> dict[str, Any]:
    by_type = Counter(blocker.blocker_type for blocker in blockers)
    return {
        "total": len(blockers),
        "by_type": dict(sorted(by_type.items())),
    }


def _owner_summary(blockers: list[EvidenceCheck]) -> dict[str, int]:
    by_owner = Counter(blocker.owner for blocker in blockers if blocker.owner)
    return dict(sorted(by_owner.items()))


def build_report(root: Path) -> dict[str, Any]:
    private_beta = _private_beta_checks(root)
    public_blockers = _public_blockers(root)

    private_beta_ready = all(check.status == "verified" for check in private_beta)
    public_ready = not public_blockers

    return {
        "private_beta": {
            "status": "ready_with_limits" if private_beta_ready else "not_ready",
            "checks": [check.as_dict() for check in private_beta],
            "boundaries": [
                "approved testers only",
                "branch-qualified local install",
                "Docker built from source",
                "hosted API finite credits",
                "no certified legacy /app UI claim",
                "no hard-site bypass guarantee",
            ],
        },
        "public_launch": {
            "status": "ready" if public_ready else "blocked",
            "blocker_summary": _blocker_summary(public_blockers),
            "owner_summary": _owner_summary(public_blockers),
            "blockers": [blocker.as_dict() for blocker in public_blockers],
        },
    }


def filter_report(
    report: dict[str, Any],
    *,
    owner: str | None = None,
    blocker_type: str | None = None,
) -> dict[str, Any]:
    """Return a display copy of the report with public blockers filtered."""
    if not owner and not blocker_type:
        return report

    owner_filter = owner.casefold() if owner else None
    type_filter = blocker_type.casefold() if blocker_type else None
    public_launch = dict(report["public_launch"])
    blockers = list(public_launch["blockers"])

    if owner_filter:
        blockers = [
            blocker
            for blocker in blockers
            if str(blocker.get("owner", "")).casefold() == owner_filter
        ]
    if type_filter:
        blockers = [
            blocker
            for blocker in blockers
            if str(blocker.get("blocker_type", "")).casefold() == type_filter
        ]

    public_launch["blockers"] = blockers
    public_launch["blocker_summary"] = _dict_blocker_summary(blockers)
    public_launch["owner_summary"] = _dict_owner_summary(blockers)
    return {
        **report,
        "public_launch": public_launch,
    }


def _dict_blocker_summary(blockers: list[dict[str, Any]]) -> dict[str, Any]:
    by_type = Counter(str(blocker["blocker_type"]) for blocker in blockers)
    return {
        "total": len(blockers),
        "by_type": dict(sorted(by_type.items())),
    }


def _dict_owner_summary(blockers: list[dict[str, Any]]) -> dict[str, int]:
    by_owner = Counter(str(blocker["owner"]) for blocker in blockers if blocker.get("owner"))
    return dict(sorted(by_owner.items()))


def print_text_report(report: dict[str, Any]) -> None:
    private_beta = report["private_beta"]
    public_launch = report["public_launch"]

    print(f"Private beta: {private_beta['status']}")
    for check in private_beta["checks"]:
        print(f"  - {check['area']}: {check['status']} ({check['evidence']})")

    print("")
    print(f"Public launch: {public_launch['status']}")
    blocker_summary = public_launch["blocker_summary"]
    print(f"Blocker summary: {blocker_summary['total']} total")
    for blocker_type, count in blocker_summary["by_type"].items():
        print(f"  - {blocker_type}: {count}")
    owner_summary = public_launch.get("owner_summary", {})
    if owner_summary:
        print("Owner summary:")
        for owner, count in owner_summary.items():
            print(f"  - {owner}: {count}")
    for blocker in public_launch["blockers"]:
        print(f"  - {blocker['area']} [{blocker['blocker_type']}]: {blocker['note']}")
        if "owner" in blocker:
            print(f"      owner: {blocker['owner']}")
        if "next_action" in blocker:
            print(f"      next action: {blocker['next_action']}")
        if "closure_evidence" in blocker:
            print(f"      closure evidence: {blocker['closure_evidence']}")
        if "codex_actionable_now" in blocker:
            codex_actionable = str(blocker["codex_actionable_now"]).lower()
            print(f"      codex actionable now: {codex_actionable}")

    if public_launch["status"] == "blocked":
        print("")
        print(
            "Verdict: controlled private beta can continue if limits are honored; public "
            "launch is blocked."
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--require-public",
        action="store_true",
        help="Exit nonzero unless public launch is ready.",
    )
    parser.add_argument(
        "--owner",
        help="Filter displayed public launch blockers by exact owner, case-insensitive.",
    )
    parser.add_argument(
        "--blocker-type",
        help="Filter displayed public launch blockers by blocker type, case-insensitive.",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    report = build_report(root)
    display_report = filter_report(report, owner=args.owner, blocker_type=args.blocker_type)

    if args.json:
        print(json.dumps(display_report, indent=2, sort_keys=True))
    else:
        print_text_report(display_report)

    if args.require_public and report["public_launch"]["status"] != "ready":
        return 1
    if report["private_beta"]["status"] != "ready_with_limits":
        return 1
    return 0
