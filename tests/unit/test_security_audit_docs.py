from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_security_audit_report_records_dependency_and_secret_scans() -> None:
    report = _read("docs/security/security-audit-2026-06-28.md")

    assert "Scout Security Audit" in report
    assert "Dependency CVE Scan" in report
    assert "Secret Scan" in report
    assert "Entropy-Aware Secret Scan" in report
    assert "python3 -m pip_audit" in report
    assert "git grep" in report
    assert "detect-secrets scan" in report
    assert "Result:" in report
    assert "Remaining Risks" in report
    assert "No secret values are reproduced in this report" in report


def test_release_checklist_marks_recorded_security_scans() -> None:
    checklist = _read("docs/product/release-checklist.md")

    assert "- [x] Dependency CVE scan run and recorded." in checklist
    assert "- [x] Secret scan run and recorded." in checklist
    assert "- [x] Entropy-aware secret scan run and recorded." in checklist
    assert "docs/security/security-audit-2026-06-28.md" in checklist


def test_hosted_ssrf_review_records_admission_controls_and_limits() -> None:
    review = _read("docs/security/hosted-ssrf-review-2026-06-28.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Hosted SSRF Review" in review
    assert "Admission-layer control implemented and tested" in review
    assert "DNS-resolved unsafe IPs" in review
    assert "url`, `targets`, and" in review
    assert "deployment egress policy" in review
    assert "redirect/retry validation" in review
    assert "- [x] Hosted SSRF checks reviewed." in checklist
    assert "docs/security/hosted-ssrf-review-2026-06-28.md" in checklist
    assert "Hosted artifact authorization and path confinement reviewed" in checklist


def test_hosted_artifact_authorization_review_records_current_boundary() -> None:
    review = _read("docs/security/hosted-artifact-authorization-review-2026-06-28.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Hosted Artifact Authorization Review" in review
    assert "persisted `tenant_id` ownership" in review
    assert "known allowlist of artifact names" in review
    assert "inside the persisted run" in review
    assert "/records` now uses the same hosted artifact confinement helper" in review
    assert "object storage" in review
    assert "- [x] Hosted artifact authorization and path confinement reviewed." in checklist
    assert "docs/security/hosted-artifact-authorization-review-2026-06-28.md" in checklist


def test_hosted_key_generation_and_delivery_review_records_beta_boundary() -> None:
    review = _read("docs/security/hosted-key-generation-delivery-review-2026-06-28.md")
    checklist = _read("docs/product/release-checklist.md")

    assert "Hosted API Key Generation And Delivery Review" in review
    assert "operator CLI" in review
    assert "Stripe webhook" in review
    assert "fake SMTP" in review
    assert "non-production test recipient" in review
    assert "raw API key is not stored" in review
    assert "live SMTP provider smoke remains pending" in review
    assert "- [x] Hosted API key generation flow verified." in checklist
    assert (
        "- [x] Key delivery email flow verified with a non-production test recipient." in checklist
    )
    assert "docs/security/hosted-key-generation-delivery-review-2026-06-28.md" in checklist
