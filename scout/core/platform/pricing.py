"""Hosted Scout credit packages and unit-economics helpers."""

from __future__ import annotations

from math import ceil

from pydantic import BaseModel, Field

from scout.core.platform.hosted import HostedAction, HostedPlan

COMPANY_DOSSIER_CREDIT_COST = 200
"""Standard credits for one representative company dossier crawl (~200, varies by site size).

Locked in docs/product/pricing-model-2026-07-06.md, "Credit -> capability": this is the
single reference figure used across customer summaries and economics helpers so the
dossier-to-credit conversion never drifts between packages.
"""


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
    is_subscription: bool = False
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
    """Editable assumptions used to test whether a package can make money.

    ``standard_credit_cost_cents`` is calibrated near-zero per the locked 2026-07-06
    pricing model: Scout is self-hosted with no per-call LLM cost, so the marginal
    cost of serving one more standard credit is close to $0 (see
    docs/product/pricing-model-2026-07-06.md, "Unit economics"). The binding
    constraint on volume is shared VPS/hardware capacity, not variable dollar cost.
    """

    fixed_monthly_cost_cents: int = Field(default=12_000, ge=0)
    standard_credit_cost_cents: float = Field(default=0.01, ge=0)
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
        standard_credits=5000,
        browser_credits=100,
        trial_days=30,
        requires_payment_method=True,
        is_public_purchase=False,
        customer_summary=(
            "30-day beta trial with 5,000 standard credits and 100 browser credits for "
            "registered beta testers — enough to exercise every Scout feature end to end."
        ),
    ),
    "free_ga": HostedCreditPackage(
        package_id="free_ga",
        name="Free GA",
        hosted_plan=HostedPlan.LOCAL_FREE,
        amount_cents=0,
        standard_credits=5000,
        browser_credits=0,
        trial_days=0,
        requires_payment_method=False,
        is_public_purchase=True,
        is_subscription=False,
        customer_summary=(
            "5,000 standard credits, free, one-time: roughly 5,000 pages, 25 company "
            "dossiers at ~200 credits each, or 2 product catalogs. Scout's public GA "
            "acquisition tier — no subscription required."
        ),
    ),
    "standard_1000": HostedCreditPackage(
        package_id="standard_1000",
        name="Standard Credits 1000",
        hosted_plan=HostedPlan.HOSTED_STARTER,
        amount_cents=1000,
        standard_credits=10000,
        browser_credits=0,
        trial_days=0,
        requires_payment_method=True,
        is_public_purchase=True,
        customer_summary=(
            "10,000 standard credits for $10: roughly 10,000 scrapes, 10,000 returned crawl "
            "pages, 3,333 screenshots, 10,000 product/intelligence records, or 50 company "
            "dossiers before heavier browser work."
        ),
    ),
    "standard_3000": HostedCreditPackage(
        package_id="standard_3000",
        name="Standard Credits 3000",
        hosted_plan=HostedPlan.HOSTED_STARTER,
        amount_cents=2500,
        standard_credits=30000,
        browser_credits=0,
        trial_days=0,
        requires_payment_method=True,
        is_public_purchase=True,
        customer_summary=(
            "30,000 standard credits for $25 — a volume discount for recurring API users "
            "(150 company dossiers at ~200 credits each)."
        ),
    ),
    "standard_15000": HostedCreditPackage(
        package_id="standard_15000",
        name="Standard Credits 15000",
        hosted_plan=HostedPlan.HOSTED_PRO,
        amount_cents=10000,
        standard_credits=150000,
        browser_credits=0,
        trial_days=0,
        requires_payment_method=True,
        is_public_purchase=True,
        customer_summary=(
            "150,000 standard credits for $100 for heavier teams once support and abuse "
            "controls are proven (750 company dossiers at ~200 credits each)."
        ),
    ),
    "unlimited_monthly": HostedCreditPackage(
        package_id="unlimited_monthly",
        name="Monthly Subscription",
        hosted_plan=HostedPlan.HOSTED_UNLIMITED,
        amount_cents=1200,
        standard_credits=50000,
        browser_credits=0,
        trial_days=0,
        requires_payment_method=True,
        is_public_purchase=True,
        is_subscription=True,
        customer_summary=(
            "$12/month: 50,000 credits / month — 20,000 page operations (scrape, crawl, "
            "map, screenshot) + 10,000 products + 100 company dossiers at ~200 credits "
            "each, resetting every billing cycle."
        ),
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
        "company_dossier": f"~{COMPANY_DOSSIER_CREDIT_COST} standard credits per dossier",
    }


def dossiers_per_package(package_id: str) -> int:
    """Return how many ~200-credit company dossiers a package's standard credits cover."""
    package = get_credit_package(package_id)
    return package.standard_credits // COMPANY_DOSSIER_CREDIT_COST


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
        standard_1000_credits = get_credit_package("standard_1000").standard_credits
        included_in_standard_1000 = standard_1000_credits // action.credit_cost
    return HostedCreditPolicy(
        action=action.value,
        credit_type=action.credit_type,
        credits_per_unit=action.credit_cost,
        metered_unit=metered_unit,
        included_in_standard_1000=included_in_standard_1000,
        customer_description=customer_description,
    )
