"""Research runner — scrapes target URL(s) and extracts content summaries."""

from __future__ import annotations

import re

from scout.core.crawler import ScoutCrawler
from scout.core.platform.types import RunRequest
from scout.core.use_cases.intelligence import ResearchRecord
from scout.core.use_cases.runners.base import (
    evidence_from_scrape,
    make_citation,
    safe_scrape,
)


def _extract_summary(markdown: str, limit: int = 600) -> str:
    lines = [ln.strip() for ln in markdown.split("\n") if ln.strip() and not ln.startswith("#")]
    text = " ".join(lines)
    return text[:limit].strip()


def _extract_title(markdown: str) -> str:
    match = re.search(r"(?m)^#\s+(.+)$", markdown)
    return match.group(1).strip() if match else ""


async def run_research(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    targets = req.targets or ([req.url] if req.url else [])
    if not targets:
        return []

    records: list[dict] = []
    topic = req.query or "research"
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower())[:40].strip("_")

    for i, url in enumerate(targets[:10]):
        resp = await safe_scrape(crawler, url)
        if not resp:
            continue

        source = evidence_from_scrape(url, resp)
        title = _extract_title(resp.markdown) or url.split("/")[-1] or "Research page"
        summary = _extract_summary(resp.markdown)

        records.append(
            ResearchRecord(
                objectID=f"research_{slug}_{i}",
                topic=topic,
                url=url,
                title=title,
                summary=summary,
                source_url=url,
                confidence=0.7 if summary else 0.4,
                citations=[make_citation(source, "url", url, summary[:200])],
            ).model_dump(mode="json")
        )

    return records
