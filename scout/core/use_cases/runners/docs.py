"""Docs runner — shallow crawl of documentation site, extract page titles + summaries."""

from __future__ import annotations

import re

from scout.core.crawler import ScoutCrawler
from scout.core.platform.types import RunRequest
from scout.core.use_cases.intelligence import ResearchRecord
from scout.core.use_cases.runners.base import now_iso
from scout.core.platform.types import (
    Citation,
    FetchProviderKind,
    FetchResult,
    SourceEvidence,
)
from scout.core.types import CrawlRequest


def _summary(markdown: str, limit: int = 400) -> str:
    lines = [ln.strip() for ln in markdown.split("\n") if ln.strip() and not ln.startswith("#")]
    return " ".join(lines)[:limit].strip()


def _title(markdown: str) -> str:
    match = re.search(r"(?m)^#\s+(.+)$", markdown)
    return match.group(1).strip() if match else ""


async def run_docs(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    url = req.url or (req.targets[0] if req.targets else "")
    if not url:
        return []

    topic = req.query or "docs"
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower())[:40].strip("_")

    try:
        crawl_resp = await crawler.crawl(
            CrawlRequest(url=url, max_depth=2, max_pages=15, use_js=True, timeout_ms=60000)
        )
    except Exception:
        return []

    if not crawl_resp.success or not crawl_resp.pages:
        return []

    records: list[dict] = []
    for i, page in enumerate(crawl_resp.pages):
        if not page.success or not page.markdown.strip():
            continue

        title = _title(page.markdown) or page.url.split("/")[-1] or f"Doc page {i}"
        summary = _summary(page.markdown)

        source = FetchResult(
            evidence=SourceEvidence(
                provider=FetchProviderKind.CRAWL4AI,
                source_url=page.url,
                final_url=page.url,
                fetched_at=now_iso(),
                confidence=0.8,
            ),
            markdown=page.markdown,
            text=page.markdown,
        )

        records.append(
            ResearchRecord(
                objectID=f"docs_{slug}_{i}",
                topic=topic,
                url=page.url,
                title=title,
                summary=summary,
                source_url=page.url,
                confidence=0.75 if summary else 0.4,
                citations=[
                    Citation(
                        source_id=source.evidence.source_id,
                        source_url=page.url,
                        field="url",
                        claim=title,
                        snippet=summary[:200],
                        confidence=0.75,
                    )
                ],
            ).model_dump(mode="json")
        )

    return records
