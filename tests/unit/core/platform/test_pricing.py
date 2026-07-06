"""Tests for hosted Scout credit packaging and unit economics."""

from __future__ import annotations

from scout.core.platform.hosted import HostedPlan
from scout.core.platform.pricing import (
    COMPANY_DOSSIER_CREDIT_COST,
    DEFAULT_UNIT_ECONOMICS,
    credit_cost_table,
    credit_packages,
    dossiers_per_package,
    get_credit_package,
    package_unit_economics,
)


def test_pay_as_you_go_1000_credit_pack_defines_customer_value() -> None:
    package = get_credit_package("standard_1000")

    assert package.amount_cents == 1000
    assert package.hosted_plan is HostedPlan.HOSTED_STARTER
    assert package.currency == "usd"
    assert package.standard_credits == 10000
    assert package.browser_credits == 0
    assert package.customer_summary == (
        "10,000 standard credits for $10: roughly 10,000 scrapes, 10,000 returned crawl "
        "pages, 3,333 screenshots, 10,000 product/intelligence records, or 50 company "
        "dossiers before heavier browser work."
    )


def test_standard_3000_pack_reprices_to_thirty_thousand_credits() -> None:
    package = get_credit_package("standard_3000")

    assert package.amount_cents == 2500
    assert package.standard_credits == 30000
    assert package.customer_summary == (
        "30,000 standard credits for $25 — a volume discount for recurring API users "
        "(150 company dossiers at ~200 credits each)."
    )


def test_standard_15000_pack_reprices_to_one_hundred_fifty_thousand_credits() -> None:
    package = get_credit_package("standard_15000")

    assert package.amount_cents == 10000
    assert package.standard_credits == 150000
    assert package.customer_summary == (
        "150,000 standard credits for $100 for heavier teams once support and abuse "
        "controls are proven (750 company dossiers at ~200 credits each)."
    )


def test_free_ga_package_is_the_public_zero_cost_acquisition_tier() -> None:
    package = get_credit_package("free_ga")

    assert package.amount_cents == 0
    assert package.currency == "usd"
    assert package.standard_credits == 5000
    assert package.browser_credits == 0
    assert package.trial_days == 0
    assert package.requires_payment_method is False
    assert package.is_public_purchase is True
    assert package.is_subscription is False
    assert package.hosted_plan is HostedPlan.LOCAL_FREE
    assert "unlimited" not in package.customer_summary.lower()
    assert package.customer_summary == (
        "5,000 standard credits, free, one-time: roughly 5,000 pages, 25 company "
        "dossiers at ~200 credits each, or 2 product catalogs. Scout's public GA "
        "acquisition tier — no subscription required."
    )


def test_no_customer_summary_ever_uses_the_word_unlimited() -> None:
    for package in credit_packages():
        assert "unlimited" not in package.customer_summary.lower(), (
            f"{package.package_id} customer_summary must not say 'unlimited'"
        )


def test_beta_trial_package_is_free_limited_and_timeboxed() -> None:
    package = get_credit_package("beta_trial")

    assert package.hosted_plan is HostedPlan.HOSTED_BETA_PASS
    assert package.amount_cents == 0
    assert package.standard_credits == 5000
    assert package.browser_credits == 100
    assert package.trial_days == 30
    assert package.requires_payment_method is True
    assert package.is_public_purchase is False


def test_high_volume_package_maps_to_pro_plan_limits() -> None:
    package = get_credit_package("standard_15000")

    assert package.hosted_plan is HostedPlan.HOSTED_PRO


def test_paid_packages_default_to_one_time_not_subscription() -> None:
    package = get_credit_package("standard_1000")

    assert package.is_subscription is False


def test_unlimited_monthly_package_is_a_recurring_subscription() -> None:
    package = get_credit_package("unlimited_monthly")

    assert package.amount_cents == 1200
    assert package.currency == "usd"
    assert package.standard_credits == 50000
    assert package.browser_credits == 0
    assert package.trial_days == 0
    assert package.requires_payment_method is True
    assert package.is_public_purchase is True
    assert package.is_subscription is True
    assert package.hosted_plan is HostedPlan.HOSTED_UNLIMITED
    assert "unlimited" not in package.customer_summary.lower()
    assert package.customer_summary == (
        "$12/month: 50,000 credits / month — 20,000 page operations (scrape, crawl, "
        "map, screenshot) + 10,000 products + 100 company dossiers at ~200 credits "
        "each, resetting every billing cycle."
    )


def test_credit_cost_table_explains_what_one_credit_means() -> None:
    table = credit_cost_table()

    assert table["scrape"] == "1 standard credit"
    assert table["crawl_page"] == "1 standard credit per returned page"
    assert table["browser_minute"] == "10 browser credits per minute"
    assert table["company_dossier"] == "~200 standard credits per dossier"


def test_company_dossier_credit_cost_is_standardized_at_200() -> None:
    assert COMPANY_DOSSIER_CREDIT_COST == 200


def test_dossiers_per_package_uses_the_standardized_dossier_cost() -> None:
    assert dossiers_per_package("free_ga") == 25
    assert dossiers_per_package("standard_1000") == 50
    assert dossiers_per_package("standard_3000") == 150
    assert dossiers_per_package("standard_15000") == 750
    assert dossiers_per_package("unlimited_monthly") == 250


def test_unit_economics_for_1000_credit_pack_meets_default_margin_target() -> None:
    economics = package_unit_economics("standard_1000", DEFAULT_UNIT_ECONOMICS)

    assert economics.revenue_cents == 1000
    assert economics.variable_cost_cents == 100
    assert economics.payment_fee_cents == 59
    assert economics.loaded_cost_cents == 209
    assert economics.gross_profit_cents == 791
    assert economics.gross_margin_percent == 79.1
    assert economics.target_margin_met is True
    assert economics.break_even_packages_per_month == 16


def test_unit_economics_marks_low_margin_when_costs_are_too_high() -> None:
    stressed = DEFAULT_UNIT_ECONOMICS.model_copy(
        update={"standard_credit_cost_cents": 0.8, "allocated_support_cost_cents": 250}
    )

    economics = package_unit_economics("standard_1000", stressed)

    assert economics.target_margin_met is False
    assert economics.gross_margin_percent < DEFAULT_UNIT_ECONOMICS.target_gross_margin_percent


def test_beta_grant_and_plan_limits_never_drift_apart() -> None:
    """Anti-drift guard (Arijit, 2026-07-06): the free/beta credit number lives in
    the package definition and the plan limits — they must always agree, so no
    public surface can advertise a number the backend doesn't grant."""
    from scout.core.platform.hosted import plan_limits

    package = get_credit_package("beta_trial")
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

    assert package.standard_credits == limits.standard_credits
    assert package.browser_credits == limits.browser_credits
    assert package.standard_credits == 5000
