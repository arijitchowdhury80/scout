from scout.core.modes.products import _empty_product_evidence


def test_empty_product_evidence_records_no_product_records_reason() -> None:
    evidence = _empty_product_evidence(
        start_url="https://www.nike.com/w/mens-shirts-tops-9om13znik1",
        fallback_attempted=True,
    )

    assert evidence.url == "https://www.nike.com/w/mens-shirts-tops-9om13znik1"
    assert evidence.reason == "no_product_records"
    assert evidence.fallback_attempted is True
    assert evidence.title == "No product records extracted"
