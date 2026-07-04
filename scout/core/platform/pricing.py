"""Hosted Scout credit packages and unit-economics helpers."""

from __future__ import annotations

from math import ceil

from pydantic import BaseModel, Field

from scout.core.platform.hosted import HostedAction, HostedPlan


class HostedCreditPackage(BaseModel):
    """Commercial package definition for hosted credits."""

    package_id: str
    name: str
    hosted_plan: HostedPlan
    amount_cents: int = Field(ge=0)
    currency: str = "usd"
    standard_credits: int = Field(ge=0)
    browser_credits: int = Field(ge=0)
    trial_days: int = Field(ge=0)
    requires_payment_method: bool
    is_public_purchase: bool
    customer_summary: str


class HostedCreditPolicy(BaseModel):
    """Structured customer-facing policy for one metered hosted action."""

    action: str
    credit_type: str
    credits_per_unit: int
    metered_unit: str
    included_in_standard_1000: int
    customer_description: str


class UnitEconomicsAssumptions(BaseModel):
    """Editable assumptions used to test whether a package can make money."""

    fixed_monthly_cost_cents: int = Field(default=12_000, ge=0)
    standard_credit_cost_cents: float = Field(default=0.15, ge=0)
    browser_credit_cost_cents: float = Field(default=2.0, ge=0)
    allocated_support_cost_cents: int = Field(default=50, ge=0)
    payment_percent_fee: float = Field(default=2.9, ge=0)
    payment_fixed_fee_cents: int = Field(default=30, ge=0)
    target_gross_margin_percent: float = Field(default=70.0, ge=0, le=100)


class PackageUnitEconomics(BaseModel):
    """Calculated economics for one credit package."""

    package_id: str
    revenue_cents: int
    variable_cost_cents: int
    payment_fee_cents: int
    allocated_support_cost_cents: int
    loaded_cost_cents: int
    gross_profit_cents: int
    gross_margin_percent: float
    target_margin_met: bool
    break_even_packages_per_month: int


DEFAULT_UNIT_ECONOMICS = UnitEconomicsAssumptions()

_PACKAGES = {
    "beta_trial": HostedCreditPackage(
        package_id="beta_trial",
        name="Hosted Beta Trial",
        hosted_plan=HostedPlan.HOSTED_BETA_PASS,
        amount_cents=0,
        standard_credits=100,
        browser_credits=0,
        trial_days=30,
        requires_payment_method=True,
        is_public_purchase=False,
        customer_summary=(
            "30-day beta trial with 100 standard credits for registered beta testers. "
            "Browser-heavy work is excluded until the paid browser-cost model is validated."
        ),
    ),
    "standard_1000": HostedCreditPackage(
        package_id="standard_1000",
        name="Standard Credits 1000",
        hosted_plan=HostedPlan.HOSTED_STARTER,
        amount_cents=1000,
        standard_credits=1000,
        browser_credits=0,
        trial_days=0,
        requires_payment_method=True,
        is_public_purchase=True,
        customer_summary=(
            "1,000 standard credits: roughly 1,000 scrapes, 1,000 returned crawl pages, "
            "333 screenshots, or 1,000 product/intelligence records before heavier browser work."
        ),
    ),
    "standard_3000": HostedCreditPackage(
        package_id="standard_3000",
        name="Standard Credits 3000",
        hosted_plan=HostedPlan.HOSTED_STARTER,
        amount_cents=2500,
        standard_credits=3000,
        browser_credits=0,
        trial_days=0,
        requires_payment_method=True,
        is_public_purchase=True,
        customer_summary="3,000 standard credits for recurring API users with a modest volume discount.",
    ),
    "standard_15000": HostedCreditPackage(
        package_id="standard_15000",
        name="Standard Credits 15000",
        hosted_plan=HostedPlan.HOSTED_PRO,
        amount_cents=10000,
        standard_credits=15000,
        browser_credits=0,
        trial_days=0,
        requires_payment_method=True,
        is_public_purchase=True,
        customer_summary="15,000 standard credits for heavier teams once support and abuse controls are proven.",
    ),
    "browser_100": HostedCreditPackage(
        package_id="browser_100",
        name="Browser Credits 100",
        hosted_plan=HostedPlan.HOSTED_STARTER,
        amount_cents=2000,
        standard_credits=0,
        browser_credits=100,
        trial_days=0,
        requires_payment_method=True,
        is_public_purchase=False,
        customer_summary=(
            "100 browser credits: roughly 20 browser renders or 10 browser minutes. "
            "This stays private until browser-worker costs are validated."
        ),
    ),
}


def credit_packages() -> list[HostedCreditPackage]:
    """Return all hosted credit packages in display order."""
    return list(_PACKAGES.values())


def get_credit_package(package_id: str) -> HostedCreditPackage:
    """Return one hosted credit package by stable id."""
    try:
        return _PACKAGES[package_id]
    except KeyError as exc:
        raise ValueError(f"Unknown hosted credit package: {package_id}") from exc


def credit_cost_table() -> dict[str, str]:
    """Return customer-facing credit meanings for hosted actions."""
    return {
        HostedAction.SCRAPE.value: "1 standard credit",
        HostedAction.CRAWL_PAGE.value: "1 standard credit per returned page",
        HostedAction.SCREENSHOT.value: "3 standard credits",
        HostedAction.BROWSER_RENDER.value: "5 browser credits per render",
        HostedAction.BROWSER_MINUTE.value: "10 browser credits per minute",
    }


def credit_policy_table() -> list[HostedCreditPolicy]:
    """Return structured metering rules for hosted packages and documentation."""
    return [
        _credit_policy(
            HostedAction.SCRAPE,
            "request",
            "Fetch one public URL and return the requested hosted scrape formats.",
        ),
        _credit_policy(
            HostedAction.CRAWL_PAGE,
            "returned page",
            "Return one discovered crawl/map page within hosted plan limits.",
        ),
        _credit_policy(
            HostedAction.SCREENSHOT,
            "screenshot",
            "Capture one screenshot artifact for a public URL.",
        ),
        _credit_policy(
            HostedAction.BROWSER_RENDER,
            "browser render",
            "Run one hosted browser render when browser credits are enabled.",
        ),
        _credit_policy(
            HostedAction.BROWSER_MINUTE,
            "browser minute",
            "Consume one minute of hosted browser execution when browser credits are enabled.",
        ),
    ]


def package_unit_economics(
    package_id: str,
    assumptions: UnitEconomicsAssumptions = DEFAULT_UNIT_ECONOMICS,
) -> PackageUnitEconomics:
    """Calculate package margin and break-even units under explicit assumptions."""
    package = get_credit_package(package_id)
    variable_cost = round(
        package.standard_credits * assumptions.standard_credit_cost_cents
        + package.browser_credits * assumptions.browser_credit_cost_cents
    )
    payment_fee = 0
    if package.amount_cents > 0:
        payment_fee = round(
            package.amount_cents * assumptions.payment_percent_fee / 100
            + assumptions.payment_fixed_fee_cents
        )
    loaded_cost = variable_cost + payment_fee + assumptions.allocated_support_cost_cents
    gross_profit = package.amount_cents - loaded_cost
    gross_margin = _percent(gross_profit, package.amount_cents)
    break_even = 0
    if gross_profit > 0:
        break_even = ceil(assumptions.fixed_monthly_cost_cents / gross_profit)
    return PackageUnitEconomics(
        package_id=package.package_id,
        revenue_cents=package.amount_cents,
        variable_cost_cents=variable_cost,
        payment_fee_cents=payment_fee,
        allocated_support_cost_cents=assumptions.allocated_support_cost_cents,
        loaded_cost_cents=loaded_cost,
        gross_profit_cents=gross_profit,
        gross_margin_percent=gross_margin,
        target_margin_met=gross_margin >= assumptions.target_gross_margin_percent,
        break_even_packages_per_month=break_even,
    )


def _percent(numerator: int, denominator: int) -> float:
    """Return percentage rounded to one decimal place, guarding zero revenue."""
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator * 100, 1)


def _credit_policy(
    action: HostedAction,
    metered_unit: str,
    customer_description: str,
) -> HostedCreditPolicy:
    """Build one structured policy row from the canonical hosted action enum."""
    included_in_standard_1000 = 0
    if action.credit_type == "standard":
        included_in_standard_1000 = 1000 // action.credit_cost
    return HostedCreditPolicy(
        action=action.value,
        credit_type=action.credit_type,
        credits_per_unit=action.credit_cost,
        metered_unit=metered_unit,
        included_in_standard_1000=included_in_standard_1000,
        customer_description=customer_description,
    )
