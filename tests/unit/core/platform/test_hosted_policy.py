"""Tests for hosted Scout plan and credit policy.

# Scenario list:
# - local plan is free but not hosted-enabled
# - hosted beta pass has finite credits and retention
# - standard scrape cost is lower than browser render cost
# - usage is allowed when enough credits remain
# - usage is denied when credits are insufficient
# - unknown action names are rejected by enum validation
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from scout.core.platform.hosted import (
    HostedAction,
    HostedPlan,
    HostedUsageBalance,
    HostedUsageDecision,
    check_hosted_usage,
    plan_limits,
)


def test_plan_limits_local_is_free_but_not_hosted_enabled() -> None:
    limits = plan_limits(HostedPlan.LOCAL_FREE)

    assert limits.hosted_enabled is False
    assert limits.standard_credits == 0
    assert limits.browser_credits == 0


def test_plan_limits_beta_pass_has_finite_credits_and_retention() -> None:
    limits = plan_limits(HostedPlan.HOSTED_BETA_PASS)

    assert limits.hosted_enabled is True
    assert limits.standard_credits == 2000
    assert limits.browser_credits == 100
    assert limits.artifact_retention_days == 7
    assert limits.max_pages_per_run == 100


def test_hosted_action_browser_render_costs_more_than_scrape() -> None:
    assert HostedAction.BROWSER_RENDER.credit_cost > HostedAction.SCRAPE.credit_cost


def test_check_hosted_usage_allows_when_enough_credits_remain() -> None:
    decision = check_hosted_usage(
        HostedUsageBalance(standard_credits_remaining=10, browser_credits_remaining=5),
        HostedAction.SCRAPE,
    )

    assert decision == HostedUsageDecision(allowed=True, credit_type="standard", cost=1)


def test_check_hosted_usage_denies_when_credits_are_insufficient() -> None:
    decision = check_hosted_usage(
        HostedUsageBalance(standard_credits_remaining=2, browser_credits_remaining=0),
        HostedAction.BROWSER_RENDER,
    )

    assert decision.allowed is False
    assert decision.credit_type == "browser"
    assert decision.cost == HostedAction.BROWSER_RENDER.credit_cost
    assert "Insufficient browser credits" in decision.reason


def test_hosted_action_rejects_unknown_action() -> None:
    with pytest.raises(ValidationError):
        HostedUsageDecision(action="infinite_crawl", allowed=True, credit_type="standard", cost=1)
