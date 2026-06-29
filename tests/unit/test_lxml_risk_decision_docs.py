from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_crawl4ai_lxml_risk_decision_records_private_beta_options() -> None:
    decision = _read("docs/security/crawl4ai-lxml-risk-decision-2026-06-28.md")

    assert "Crawl4AI/lxml Risk Decision" in decision
    assert "Status: Decision required" in decision
    assert "PYSEC-2026-87" in decision
    assert "lxml 5.4.0" in decision
    assert "lxml 6.1.0" in decision
    assert "Crawl4AI" in decision
    assert "Private beta" in decision
    assert "Public launch" in decision
    assert "Option A" in decision
    assert "Option B" in decision
    assert "Option C" in decision
    assert "Recommended decision" in decision
    assert "crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md" in decision


def test_crawl4ai_lxml_exception_packet_is_decision_ready_but_not_approved() -> None:
    packet = _read("docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md")

    assert "Crawl4AI/lxml Private-Beta Exception Packet" in packet
    assert "Status: Proposed exception packet; not approved" in packet
    assert "limited private-beta-only security exception" in packet
    assert "PYSEC-2026-87" in packet
    assert "`lxml 5.4.0`" in packet
    assert "`lxml 6.1.0`" in packet
    assert "public launch" in packet
    assert "Out of scope even if approved" in packet
    assert "dependency-audit CI job remains visible" in packet
    assert "hosted SSRF protections remain enabled" in packet
    assert "hosted artifact authorization remains enforced" in packet
    assert "Exit criteria" in packet
    assert "Approve limited private-beta exception only" in packet
    assert "Reject exception" in packet
    assert "This packet is currently **not approved**." in packet


def test_release_checklist_requires_lxml_risk_decision_before_public_launch() -> None:
    checklist = _read("docs/product/release-checklist.md")

    assert "- [ ] Crawl4AI/lxml risk decision approved." in checklist
    assert "docs/security/crawl4ai-lxml-risk-decision-2026-06-28.md" in checklist
    assert "docs/security/crawl4ai-lxml-private-beta-exception-packet-2026-06-29.md" in checklist
    assert "Public launch remains blocked" in checklist
