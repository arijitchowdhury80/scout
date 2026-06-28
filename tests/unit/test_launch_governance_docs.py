from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_security_policy_defines_private_reporting_and_supported_scope() -> None:
    policy = _read("SECURITY.md")

    assert "Private Beta Security Policy" in policy
    assert "Do not open a public GitHub issue for security reports" in policy
    assert "Supported Versions" in policy
    assert "Hosted Scout" in policy
    assert "Local Scout" in policy
    assert "Security Review Checklist" in policy
    assert "SSRF" in policy
    assert "API key" in policy
    assert "secrets" in policy.lower()


def test_private_beta_issue_templates_exist_and_route_feedback() -> None:
    bug_report = ROOT / ".github" / "ISSUE_TEMPLATE" / "private_beta_bug.yml"
    feature_request = ROOT / ".github" / "ISSUE_TEMPLATE" / "private_beta_feature.yml"

    for template in [bug_report, feature_request]:
        assert template.exists()
        parsed = yaml.safe_load(template.read_text(encoding="utf-8"))
        assert parsed["labels"]
        assert any("private-beta" in label for label in parsed["labels"])
        assert parsed["body"]

    bug_template = yaml.safe_load(bug_report.read_text(encoding="utf-8"))
    feature_template = yaml.safe_load(feature_request.read_text(encoding="utf-8"))

    bug_text = bug_report.read_text(encoding="utf-8")
    assert bug_template["name"] == "Private beta bug"
    assert "Scout version" in bug_text
    assert "Local package, Docker, hosted API, or skill" in bug_text
    assert "Logs, run ID, or artifact path" in bug_text

    feature_text = feature_request.read_text(encoding="utf-8")
    assert feature_template["name"] == "Private beta feature request"
    assert "Product, company intel, hosted API, local CLI, or distribution" in feature_text
    assert "What workflow are you trying to complete?" in feature_text


def test_release_checklist_blocks_public_launch_until_decisions_are_closed() -> None:
    checklist = _read("docs/product/release-checklist.md")

    required_gates = [
        "License decision recorded",
        "GitHub release artifact workflow",
        "Clean wheel install smoke",
        "Docker runtime smoke",
        "Hosted economics and usage limits",
        "Security policy",
        "Private beta feedback templates",
        "Third-party notices",
        "No public registry publish",
    ]
    for gate in required_gates:
        assert gate in checklist

    assert "Public launch is blocked until" in checklist
    assert "PyPI" in checklist
    assert "GHCR" in checklist
    assert "Docker Hub" in checklist


def test_hosted_economics_and_usage_limits_are_documented_without_approval() -> None:
    economics = _read("docs/product/hosted-economics-and-usage-limits.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Hosted Economics And Usage Limits" in economics
    assert "$22 one-time hosted beta pass" in economics
    assert "finite hosted credits" in economics
    assert "No unlimited hosted crawling" in economics
    assert "Standard credits | 2,000" in economics
    assert "Browser credits | 100" in economics
    assert "Browser render | browser | 5" in economics
    assert "Browser minute | browser | 10" in economics
    assert "Firecrawl" in economics
    assert "Browserbase" in economics
    assert "Subscriptions can follow after private-beta usage data is measured" in economics
    assert "- [ ] Public launch pricing and hosted usage limits approved." in checklist
    assert (
        "- [x] Hosted economics and usage limits documented against the `$22` beta pass"
        in checklist
    )
    assert "docs/product/hosted-economics-and-usage-limits.md" in checklist
