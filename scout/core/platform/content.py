"""Helpers for turning host or saved content into normalized fetch results."""

from __future__ import annotations

from scout.core.platform.types import FetchProviderKind, FetchResult, SourceEvidence


def fetch_result_from_markdown(
    markdown: str,
    source_url: str,
    provider: FetchProviderKind,
    fetched_at: str,
    final_url: str = "",
) -> FetchResult:
    return FetchResult(
        evidence=SourceEvidence(
            provider=provider,
            source_url=source_url,
            final_url=final_url or source_url,
            fetched_at=fetched_at,
        ),
        markdown=markdown,
        text=markdown,
    )
