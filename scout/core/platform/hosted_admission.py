"""Hosted request admission for auth, URL safety, and usage debit."""

from __future__ import annotations

from pydantic import BaseModel

from scout.core.platform.account_service import HostedAccountDecision, HostedAccountService
from scout.core.platform.hosted import HostedAction, HostedUsageDecision
from scout.core.platform.url_safety import UrlSafetyResult, validate_hosted_url


class HostedAdmissionDecision(BaseModel):
    """Decision returned before accepting hosted URL work."""

    allowed: bool
    reason: str = ""
    tenant_id: str = ""
    key_id: str = ""
    url_safety: UrlSafetyResult | None = None
    usage: HostedUsageDecision | None = None


class HostedAdmissionService:
    """Composes key auth, SSRF guard, and credit debit for hosted requests."""

    def __init__(self, account_service: HostedAccountService) -> None:
        self.account_service = account_service

    def admit_url_action(
        self,
        raw_key: str,
        url: str,
        action: HostedAction,
        required_scope: str = "",
        resolved_ips: list[str] | None = None,
    ) -> HostedAdmissionDecision:
        """Return whether a hosted URL/action request should be accepted."""
        auth = self.account_service.authenticate_key(raw_key, required_scope)
        if not auth.allowed:
            return _from_account_decision(auth)

        url_safety = validate_hosted_url(url, resolved_ips=resolved_ips)
        if not url_safety.allowed:
            return HostedAdmissionDecision(
                allowed=False,
                reason=url_safety.reason,
                tenant_id=auth.tenant_id,
                key_id=auth.key_id,
                url_safety=url_safety,
            )

        usage = self.account_service.consume_action(raw_key, action, required_scope)
        return HostedAdmissionDecision(
            allowed=usage.allowed,
            reason=usage.reason,
            tenant_id=usage.tenant_id,
            key_id=usage.key_id,
            url_safety=url_safety,
            usage=usage.usage,
        )


def _from_account_decision(decision: HostedAccountDecision) -> HostedAdmissionDecision:
    """Convert account auth decisions into admission decisions."""
    return HostedAdmissionDecision(
        allowed=decision.allowed,
        reason=decision.reason,
        tenant_id=decision.tenant_id,
        key_id=decision.key_id,
        usage=decision.usage,
    )
