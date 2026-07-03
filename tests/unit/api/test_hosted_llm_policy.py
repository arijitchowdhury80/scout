"""Tests for hosted LLM spend guardrails."""

from scout.api.config import Settings
from scout.api.hosted_llm_policy import resolve_hosted_llm_api_key


def test_public_hosted_mode_disables_llm_key_even_when_env_key_exists() -> None:
    settings = Settings(
        scout_public_hosted_only=True,
        hosted_llm_mode="disabled",
        llm_api_key="expensive-real-key",
    )

    assert resolve_hosted_llm_api_key(settings) == ""


def test_non_hosted_local_mode_keeps_llm_key_for_local_extract() -> None:
    settings = Settings(
        scout_public_hosted_only=False,
        hosted_llm_mode="disabled",
        llm_api_key="local-dev-key",
    )

    assert resolve_hosted_llm_api_key(settings) == "local-dev-key"


def test_hosted_allowlist_mode_rejects_frontier_provider_names() -> None:
    settings = Settings(
        scout_public_hosted_only=True,
        hosted_llm_mode="allowlist",
        hosted_llm_provider_allowlist="ollama/llama3.2:3b",
        llm_api_key="some-key",
    )

    assert resolve_hosted_llm_api_key(settings, requested_provider="openai/gpt-5") == ""
    assert resolve_hosted_llm_api_key(settings, requested_provider="anthropic/claude-4") == ""
    assert resolve_hosted_llm_api_key(settings, requested_provider="gemini/gemini-2.0-flash") == ""
    assert (
        resolve_hosted_llm_api_key(settings, requested_provider="ollama/llama3.2:3b") == "some-key"
    )
