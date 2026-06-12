"""Provider contracts and capability metadata."""

from __future__ import annotations

from enum import Enum
from typing import Protocol

from pydantic import BaseModel

from scout.core.platform.types import FetchProviderKind, FetchResult


class ProviderRuntime(str, Enum):
    SKILL_HOST = "skill_host"
    STANDALONE = "standalone"
    BOTH = "both"


class ProviderCapability(BaseModel):
    kind: FetchProviderKind
    runtime: ProviderRuntime
    supports_discovery: bool = False
    supports_fetch: bool = True
    supports_browser_session: bool = False
    supports_documents: bool = False


class FetchProvider(Protocol):
    kind: FetchProviderKind

    async def fetch(self, url: str) -> FetchResult:
        """Fetch one URL and return normalized content."""
        ...


_PROVIDER_CAPABILITIES = {
    FetchProviderKind.CRAWL4AI: ProviderCapability(
        kind=FetchProviderKind.CRAWL4AI,
        runtime=ProviderRuntime.STANDALONE,
        supports_discovery=True,
        supports_fetch=True,
    ),
    FetchProviderKind.CDP: ProviderCapability(
        kind=FetchProviderKind.CDP,
        runtime=ProviderRuntime.STANDALONE,
        supports_fetch=True,
        supports_browser_session=True,
    ),
    FetchProviderKind.HOST_BROWSER: ProviderCapability(
        kind=FetchProviderKind.HOST_BROWSER,
        runtime=ProviderRuntime.SKILL_HOST,
        supports_fetch=True,
        supports_browser_session=True,
    ),
    FetchProviderKind.HOST_WEBFETCH: ProviderCapability(
        kind=FetchProviderKind.HOST_WEBFETCH,
        runtime=ProviderRuntime.SKILL_HOST,
        supports_fetch=True,
    ),
    FetchProviderKind.WEBSEARCH: ProviderCapability(
        kind=FetchProviderKind.WEBSEARCH,
        runtime=ProviderRuntime.SKILL_HOST,
        supports_discovery=True,
        supports_fetch=True,
    ),
    FetchProviderKind.API: ProviderCapability(
        kind=FetchProviderKind.API,
        runtime=ProviderRuntime.BOTH,
        supports_fetch=True,
    ),
    FetchProviderKind.SAVED: ProviderCapability(
        kind=FetchProviderKind.SAVED,
        runtime=ProviderRuntime.BOTH,
        supports_fetch=True,
    ),
}


def capability_for_provider(kind: FetchProviderKind) -> ProviderCapability:
    return _PROVIDER_CAPABILITIES.get(
        kind,
        ProviderCapability(kind=kind, runtime=ProviderRuntime.BOTH, supports_fetch=True),
    )
