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
