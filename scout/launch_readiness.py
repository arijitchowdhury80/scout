"""Scout private-beta and public-launch readiness checks."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvidenceCheck:
    area: str
    status: str
    evidence: str
    note: str

    def as_dict(self) -> dict[str, str]:
        return {
            "area": self.area,
            "status": self.status,
            "evidence": self.evidence,
            "note": self.note,
        }


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
    ("license decision", "- [ ] License decision recorded."),
    ("final license expression", "- [ ] Final license expression added to `pyproject.toml`."),
    ("LICENSE file", "- [ ] `LICENSE` file added if Scout is open source or source-available."),
    (
        "public pricing and hosted usage limits",
        "- [ ] Public launch pricing and hosted usage limits approved.",
    ),
    (
        "registry publishing policy",
        "- [ ] Registry publishing policy approved for PyPI, GHCR, Docker Hub, or other",
    ),
    (
        "GitHub release workflow run",
        "- [ ] GitHub release artifact workflow run against a real `v*` tag.",
    ),
    (
        "release artifact smoke",
        "- [ ] Release artifact downloaded from GitHub Release and smoke-tested locally.",
    ),
    ("Docker image publishing policy", "- [ ] Docker image publishing policy approved."),
    (
        "published Docker image smoke",
        "- [ ] Published Docker image smoke-tested if GHCR, Docker Hub, or another",
    ),
    ("Crawl4AI/lxml risk decision", "- [ ] Crawl4AI/lxml risk decision approved."),
    (
        "dependency audit blocking cleanly",
        "- [ ] Dependency audit clean and blocking in GitHub CI.",
    ),
    (
        "Stripe real test-mode smoke",
        "- [ ] Stripe checkout and webhook tested in Stripe test mode.",
    ),
]


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
    return checks


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
    for area, marker in PUBLIC_BLOCKER_LINES:
        if marker in checklist:
            blockers.append(
                EvidenceCheck(
                    area=area,
                    status="blocked",
                    evidence="docs/product/release-checklist.md",
                    note=f"Unchecked gate remains: {marker}",
                )
            )

    pyproject = _read(root / "pyproject.toml") if (root / "pyproject.toml").exists() else ""
    if 'license = "' not in pyproject:
        blockers.append(
            EvidenceCheck(
                area="pyproject license expression",
                status="blocked",
                evidence="pyproject.toml",
                note="No final project license expression is present.",
            )
        )

    if not (root / "LICENSE").exists():
        blockers.append(
            EvidenceCheck(
                area="LICENSE file",
                status="blocked",
                evidence="LICENSE",
                note="No project LICENSE file is present.",
            )
        )

    return blockers


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
            "blockers": [blocker.as_dict() for blocker in public_blockers],
        },
    }


def print_text_report(report: dict[str, Any]) -> None:
    private_beta = report["private_beta"]
    public_launch = report["public_launch"]

    print(f"Private beta: {private_beta['status']}")
    for check in private_beta["checks"]:
        print(f"  - {check['area']}: {check['status']} ({check['evidence']})")

    print("")
    print(f"Public launch: {public_launch['status']}")
    for blocker in public_launch["blockers"]:
        print(f"  - {blocker['area']}: {blocker['note']}")

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
    args = parser.parse_args(argv)

    root = args.root.resolve()
    report = build_report(root)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)

    if args.require_public and report["public_launch"]["status"] != "ready":
        return 1
    if report["private_beta"]["status"] != "ready_with_limits":
        return 1
    return 0
