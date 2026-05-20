"""Execution mode policy for Scout high-level runs."""

from __future__ import annotations

from enum import Enum

from scout.core.platform.types import FetchProviderKind


class ExecutionMode(str, Enum):
    AUTO = "auto"
    CRAWL4AI = "crawl4ai"
    WEBFETCH = "webfetch"
    WEBSEARCH = "websearch"
    BROWSER = "browser"
    SAVED = "saved"
    API = "api"


def provider_ladder_for_mode(mode: ExecutionMode) -> list[FetchProviderKind]:
    if mode == ExecutionMode.AUTO:
        return [
            FetchProviderKind.CRAWL4AI,
            FetchProviderKind.API,
            FetchProviderKind.SAVED,
            FetchProviderKind.HOST_WEBFETCH,
            FetchProviderKind.WEBSEARCH,
            FetchProviderKind.HOST_BROWSER,
        ]
    if mode == ExecutionMode.CRAWL4AI:
        return [FetchProviderKind.CRAWL4AI]
    if mode == ExecutionMode.WEBFETCH:
        return [FetchProviderKind.HOST_WEBFETCH]
    if mode == ExecutionMode.WEBSEARCH:
        return [FetchProviderKind.WEBSEARCH]
    if mode == ExecutionMode.BROWSER:
        return [FetchProviderKind.HOST_BROWSER]
    if mode == ExecutionMode.SAVED:
        return [FetchProviderKind.SAVED]
    if mode == ExecutionMode.API:
        return [FetchProviderKind.API]
    return [FetchProviderKind.CRAWL4AI]
