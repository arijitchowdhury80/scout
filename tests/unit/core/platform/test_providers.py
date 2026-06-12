from scout.core.platform.providers import (
    ProviderCapability,
    ProviderRuntime,
    capability_for_provider,
)
from scout.core.platform.types import FetchProviderKind


def test_provider_capability_marks_skill_only_provider() -> None:
    capability = ProviderCapability(
        kind=FetchProviderKind.HOST_WEBFETCH,
        runtime=ProviderRuntime.SKILL_HOST,
        supports_discovery=False,
        supports_fetch=True,
        supports_browser_session=False,
        supports_documents=False,
    )

    assert capability.kind == FetchProviderKind.HOST_WEBFETCH
    assert capability.runtime == ProviderRuntime.SKILL_HOST
    assert capability.supports_fetch is True


def test_provider_capability_marks_cli_provider() -> None:
    capability = ProviderCapability(
        kind=FetchProviderKind.CRAWL4AI,
        runtime=ProviderRuntime.STANDALONE,
        supports_discovery=True,
        supports_fetch=True,
        supports_browser_session=False,
        supports_documents=False,
    )

    assert capability.supports_discovery is True


def test_cdp_provider_capability_supports_browser_sessions() -> None:
    capability = capability_for_provider(FetchProviderKind.CDP)

    assert capability.kind == FetchProviderKind.CDP
    assert capability.runtime == ProviderRuntime.STANDALONE
    assert capability.supports_browser_session is True
