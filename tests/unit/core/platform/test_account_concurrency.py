"""Concurrency safety for hosted credit debits.

Regression guard for the TOCTOU race in ``consume_action``: a non-atomic
read-check-write let two concurrent requests both pass the balance check and
both debit, letting a tenant exceed its granted credits (double-spend / go
negative). The debit must be atomic — exactly ``balance`` actions may succeed,
never more, and the balance must never go below zero.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from scout.core.platform.account_service import (
    HostedAccountService,
    InMemoryHostedAccountStore,
)
from scout.core.platform.account_sqlite_store import SQLiteHostedAccountStore
from scout.core.platform.hosted import HostedAction, HostedPlan


def _provision_with_credits(service: HostedAccountService, credits: int) -> str:
    result = service.provision_account(
        email="racer@example.com",
        name="Racer",
        plan=HostedPlan.HOSTED_BETA_PASS,
        scopes=["runs:create"],
    )
    service.set_balance(result.tenant.tenant_id, credits, 0)
    return result.raw_api_key


@pytest.mark.parametrize("store_factory_name", ["memory", "sqlite"])
def test_concurrent_debits_never_exceed_balance(store_factory_name, tmp_path) -> None:
    if store_factory_name == "sqlite":
        store = SQLiteHostedAccountStore(tmp_path / "accounts.sqlite")
    else:
        store = InMemoryHostedAccountStore()
    service = HostedAccountService(store)

    starting_credits = 20
    attempts = 100
    raw_key = _provision_with_credits(service, starting_credits)

    def _debit(_: int) -> bool:
        decision = service.consume_action(raw_key, HostedAction.SCRAPE, "runs:create")
        return decision.allowed

    with ThreadPoolExecutor(max_workers=32) as pool:
        results = list(pool.map(_debit, range(attempts)))

    allowed = sum(1 for r in results if r)
    tenant_id = service.authenticate_key(raw_key, "runs:create").tenant_id
    final = service.get_balance(tenant_id)

    # Exactly `starting_credits` debits may succeed — never more.
    assert allowed == starting_credits, f"expected {starting_credits} allowed, got {allowed}"
    # Balance must never be driven negative.
    assert final.standard_credits_remaining == 0
