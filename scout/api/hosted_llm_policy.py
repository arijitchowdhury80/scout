"""Hosted-production LLM spend guardrails."""

from __future__ import annotations

from scout.api.config import Settings

_BLOCKED_PROVIDER_PREFIXES = (
    "anthropic/",
    "claude",
    "gemini/",
    "google/",
    "openai/",
    "gpt-",
    "azure/",
    "bedrock/",
)


def resolve_hosted_llm_api_key(
    settings: Settings,
    *,
    requested_provider: str = "",
) -> str:
    """Return the LLM API key only when hosted policy explicitly allows it."""
    if not settings.scout_public_hosted_only:
        return settings.llm_api_key

    mode = settings.hosted_llm_mode.strip().lower()
    if mode == "disabled":
        return ""
    if mode != "allowlist":
        return ""

    provider = requested_provider.strip().lower()
    if not provider:
        return ""
    if provider.startswith(_BLOCKED_PROVIDER_PREFIXES):
        return ""

    allowed = {
        item.strip().lower()
        for item in settings.hosted_llm_provider_allowlist.split(",")
        if item.strip()
    }
    if provider not in allowed:
        return ""
    return settings.llm_api_key
