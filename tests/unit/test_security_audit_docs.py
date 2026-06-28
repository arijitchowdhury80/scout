from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_security_audit_report_records_dependency_and_secret_scans() -> None:
    report = _read("docs/security/security-audit-2026-06-28.md")

    assert "Scout Security Audit" in report
    assert "Dependency CVE Scan" in report
    assert "Secret Scan" in report
    assert "python3 -m pip_audit" in report
    assert "git grep" in report
    assert "Result:" in report
    assert "Remaining Risks" in report
    assert "No secret values are reproduced in this report" in report


def test_release_checklist_marks_recorded_security_scans() -> None:
    checklist = _read("docs/product/release-checklist.md")

    assert "- [x] Dependency CVE scan run and recorded." in checklist
    assert "- [x] Secret scan run and recorded." in checklist
    assert "docs/security/security-audit-2026-06-28.md" in checklist
