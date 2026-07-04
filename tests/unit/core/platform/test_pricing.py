"""Tests for hosted Scout credit packaging and unit economics."""

from __future__ import annotations

from scout.core.platform.hosted import HostedPlan
from scout.core.platform.pricing import (
    DEFAULT_UNIT_ECONOMICS,
    credit_cost_table,
    get_credit_package,
    package_unit_economics,
)


def test_pay_as_you_go_1000_credit_pack_defines_customer_value() -> None:
    package = get_credit_package("standard_1000")

    assert package.amount_cents == 1000
    assert package.hosted_plan is HostedPlan.HOSTED_STARTER
    assert package.currency == "usd"
    assert package.standard_credits == 1000
    assert package.browser_credits == 0
    assert package.customer_summary == (
        "1,000 standard credits: roughly 1,000 scrapes, 1,000 returned crawl pages, "
        "333 screenshots, or 1,000 product/intelligence records before heavier browser work."
    )


def test_beta_trial_package_is_free_limited_and_timeboxed() -> None:
    package = get_credit_package("beta_trial")

    assert package.hosted_plan is HostedPlan.HOSTED_BETA_PASS
    assert package.amount_cents == 0
    assert package.standard_credits == 1000
    assert package.browser_credits == 100
    assert package.trial_days == 30
    assert package.requires_payment_method is True
    assert package.is_public_purchase is False


def test_high_volume_package_maps_to_pro_plan_limits() -> None:
    package = get_credit_package("standard_15000")

    assert package.hosted_plan is HostedPlan.HOSTED_PRO


def test_credit_cost_table_explains_what_one_credit_means() -> None:
    table = credit_cost_table()

    assert table["scrape"] == "1 standard credit"
    assert table["crawl_page"] == "1 standard credit per returned page"
    assert table["browser_minute"] == "10 browser credits per minute"


def test_unit_economics_for_1000_credit_pack_meets_default_margin_target() -> None:
    economics = package_unit_economics("standard_1000", DEFAULT_UNIT_ECONOMICS)

    assert economics.revenue_cents == 1000
    assert economics.variable_cost_cents == 150
    assert economics.payment_fee_cents == 59
    assert economics.loaded_cost_cents == 259
    assert economics.gross_profit_cents == 741
    assert economics.gross_margin_percent == 74.1
    assert economics.target_margin_met is True
    assert economics.break_even_packages_per_month == 17


def test_unit_economics_marks_low_margin_when_costs_are_too_high() -> None:
    stressed = DEFAULT_UNIT_ECONOMICS.model_copy(
        update={"standard_credit_cost_cents": 0.8, "allocated_support_cost_cents": 250}
    )

    economics = package_unit_economics("standard_1000", stressed)

    assert economics.target_margin_met is False
    assert economics.gross_margin_percent < DEFAULT_UNIT_ECONOMICS.target_gross_margin_percent
