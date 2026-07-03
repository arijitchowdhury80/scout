from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_unit_economics_doc_records_pay_as_you_go_candidate() -> None:
    doc = _read("docs/product/unit-economics-and-pricing-model-2026-06-29.md")

    expected = [
        "Recommended launch candidate as of 2026-07-03",
        "$10 for 1,000 standard credits",
        "1 scrape = 1 standard credit",
        "1 returned crawl page = 1 standard credit",
        "1 screenshot = 3 standard credits",
        "1 browser minute = 10 browser credits",
        "Estimated cost for 1,000 standard credits: $2.59",
        "Estimated gross margin: 74.1%",
        "Break-even: 17 packs/month",
        "Beta trial: 30 days, 100 standard credits, $0 charge, payment method required through Stripe setup-mode once hosted billing is configured",
    ]

    for marker in expected:
        assert marker in doc


def test_hosted_admin_doc_points_to_usage_and_pricing_model() -> None:
    doc = _read("docs/product/hosted-admin-operations.md")
    normalized_doc = " ".join(doc.split())

    assert "/v1/hosted/usage" in doc
    assert "/v1/hosted/purchases" in doc
    assert "/v1/billing/packages" in doc
    assert "hosted_credit_ledger" in doc
    assert "list-purchases" in doc
    assert "hosted_payment_checkouts" in doc
    assert "current public beta key request path does not require Stripe" in doc
    assert (
        "Stripe checkout is available from `/pricing` for future payment-method" in normalized_doc
    )
    assert "$10 for 1,000 standard credits" in doc
    assert "Pay-as-you-go pricing candidate" in doc


def test_stripe_redirect_examples_use_hosted_pricing_page_not_localhost() -> None:
    env_example = _read(".env.example")
    readiness = _read("docs/product/stripe-test-mode-readiness-2026-06-29.md")

    assert "STRIPE_SUCCESS_URL=https://scout.chowmes.com/pricing?checkout=success" in env_example
    assert "STRIPE_CANCEL_URL=https://scout.chowmes.com/pricing?checkout=cancelled" in env_example
    assert "STRIPE_SUCCESS_URL=https://scout.chowmes.com/pricing?checkout=success" in readiness
    assert "STRIPE_CANCEL_URL=https://scout.chowmes.com/pricing?checkout=cancelled" in readiness
    assert "STRIPE_SUCCESS_URL=http://127.0.0.1" not in env_example
    assert "STRIPE_CANCEL_URL=http://127.0.0.1" not in env_example
