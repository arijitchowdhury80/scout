import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_detect_secrets_baseline_has_only_audited_findings() -> None:
    baseline = json.loads((ROOT / ".secrets.baseline").read_text(encoding="utf-8"))
    findings = [
        finding
        for file_findings in baseline.get("results", {}).values()
        for finding in file_findings
    ]

    assert findings
    assert len(findings) == 26
    assert all(finding.get("is_secret") is False for finding in findings)


def test_detect_secrets_audit_report_documents_false_positive_review() -> None:
    report = (ROOT / "docs/security/detect-secrets-audit-2026-06-28.md").read_text(encoding="utf-8")

    assert "Detect-Secrets Candidate Audit" in report
    assert "Total candidates reviewed: 26" in report
    assert "Files with candidates: 18" in report
    assert "No candidate secret values are reproduced in this report" in report
    assert "False positive" in report
    assert "detect-secrets-hook --baseline .secrets.baseline" in report
