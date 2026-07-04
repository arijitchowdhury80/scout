"""Hosted Scout plan and usage policy primitives."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class HostedPlan(str, Enum):
    """Supported commercial plan identifiers."""

    LOCAL_FREE = "local_free"
    HOSTED_BETA_PASS = "hosted_beta_pass"
    HOSTED_STARTER = "hosted_starter"
    HOSTED_PRO = "hosted_pro"


class HostedAction(str, Enum):
    """Metered hosted action types."""

    SCRAPE = "scrape"
    CRAWL_PAGE = "crawl_page"
    SCREENSHOT = "screenshot"
    BROWSER_RENDER = "browser_render"
    BROWSER_MINUTE = "browser_minute"

    @property
    def credit_cost(self) -> int:
        """Return the credit cost for this action."""
        costs = {
            HostedAction.SCRAPE: 1,
            HostedAction.CRAWL_PAGE: 1,
            HostedAction.SCREENSHOT: 3,
            HostedAction.BROWSER_RENDER: 5,
            HostedAction.BROWSER_MINUTE: 10,
        }
        return costs[self]

    @property
    def credit_type(self) -> str:
        """Return which credit bucket this action consumes."""
        if self in {HostedAction.BROWSER_RENDER, HostedAction.BROWSER_MINUTE}:
            return "browser"
        return "standard"


class HostedPlanLimits(BaseModel):
    """Static limits for a hosted plan."""

    plan: HostedPlan
    hosted_enabled: bool
    standard_credits: int
    browser_credits: int
    artifact_retention_days: int
    max_pages_per_run: int
    max_concurrent_runs: int


class HostedUsageBalance(BaseModel):
    """Current remaining hosted credits."""

    standard_credits_remaining: int
    browser_credits_remaining: int


class HostedUsageDecision(BaseModel):
    """Decision returned before accepting hosted work."""

    action: HostedAction | None = None
    allowed: bool
    credit_type: str
    cost: int
    reason: str = ""


def plan_limits(plan: HostedPlan) -> HostedPlanLimits:
    """Return static hosted limits for a plan."""
    limits = {
        HostedPlan.LOCAL_FREE: HostedPlanLimits(
            plan=plan,
            hosted_enabled=False,
            standard_credits=0,
            browser_credits=0,
            artifact_retention_days=0,
            max_pages_per_run=0,
            max_concurrent_runs=0,
        ),
        HostedPlan.HOSTED_BETA_PASS: HostedPlanLimits(
            plan=plan,
            hosted_enabled=True,
            standard_credits=1000,
            browser_credits=100,
            artifact_retention_days=7,
            max_pages_per_run=25,
            max_concurrent_runs=1,
        ),
        HostedPlan.HOSTED_STARTER: HostedPlanLimits(
            plan=plan,
            hosted_enabled=True,
            standard_credits=5000,
            browser_credits=250,
            artifact_retention_days=14,
            max_pages_per_run=250,
            max_concurrent_runs=2,
        ),
        HostedPlan.HOSTED_PRO: HostedPlanLimits(
            plan=plan,
            hosted_enabled=True,
            standard_credits=25000,
            browser_credits=1500,
            artifact_retention_days=30,
            max_pages_per_run=1000,
            max_concurrent_runs=5,
        ),
    }
    return limits[plan]


def check_hosted_usage(balance: HostedUsageBalance, action: HostedAction) -> HostedUsageDecision:
    """Return whether a hosted action has enough credits."""
    remaining = _remaining_for_action(balance, action)
    cost = action.credit_cost
    credit_type = action.credit_type
    if remaining >= cost:
        return HostedUsageDecision(
            allowed=True,
            credit_type=credit_type,
            cost=cost,
        )
    return HostedUsageDecision(
        allowed=False,
        credit_type=credit_type,
        cost=cost,
        reason=f"Insufficient {credit_type} credits: need {cost}, have {remaining}.",
    )


def _remaining_for_action(balance: HostedUsageBalance, action: HostedAction) -> int:
    """Return remaining credits for an action's bucket."""
    if action.credit_type == "browser":
        return balance.browser_credits_remaining
    return balance.standard_credits_remaining
