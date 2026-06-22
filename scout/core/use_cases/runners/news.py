"""News intelligence runner — scrapes newsroom/press/blog pages."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from scout.core.crawler import ScoutCrawler
from scout.core.platform.types import RunRequest
from scout.core.use_cases.intelligence import NewsSignalRecord
from scout.core.use_cases.runners.base import (
    evidence_from_scrape,
    make_citation,
    safe_scrape,
)

_NEWS_PATHS = ["/news", "/newsroom", "/press", "/press-releases", "/blog", "/media"]

_DATE_PATTERN = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}"
    r"|"
    r"\d{4}[-/]\d{2}[-/]\d{2}"
)

_TOPIC_KEYWORDS = {
    "product_launch": re.compile(r"(?:launch|release|announce|unveil|introduce)", re.I),
    "partnership": re.compile(r"(?:partner|collaboration|alliance|integrate)", re.I),
    "funding": re.compile(r"(?:funding|raises?|series [A-Z]|invest)", re.I),
    "leadership": re.compile(r"(?:appoint|hire|join|new CEO|new CTO|new VP)", re.I),
    "acquisition": re.compile(r"(?:acquir|merger|buy|purchase)", re.I),
    "expansion": re.compile(r"(?:expand|open|new office|new market|international)", re.I),
}


def _base_url(req: RunRequest) -> str:
    if req.url:
        return req.url.rstrip("/")
    if req.targets:
        return req.targets[0].rstrip("/")
    name = req.query.strip().lower().replace(" ", "")
    return f"https://www.{name}.com"


def _company_name(req: RunRequest) -> str:
    return req.query.strip() or "unknown"


def _classify_topic(text: str) -> str:
    for topic, pattern in _TOPIC_KEYWORDS.items():
        if pattern.search(text):
            return topic
    return "company_news"


def _extract_articles(markdown: str, company: str, base_url: str) -> list[dict]:
    articles: list[dict] = []
    heading_pattern = re.compile(r"(?m)^#{1,3}\s+(.+)$")
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for match in heading_pattern.finditer(markdown):
        title = match.group(1).strip()
        if len(title) < 10 or len(title) > 200:
            continue
        if title.lower() in {"news", "newsroom", "press", "blog", "latest", "media"}:
            continue

        context_start = max(0, match.start() - 50)
        context_end = min(len(markdown), match.end() + 500)
        context = markdown[context_start:context_end]

        date_match = _DATE_PATTERN.search(context)
        link_match = link_pattern.search(context)

        url = ""
        if link_match:
            href = link_match.group(2)
            if href.startswith("/"):
                url = urljoin(base_url, href)
            elif href.startswith("http"):
                url = href

        articles.append(
            {
                "title": title,
                "url": url or base_url,
                "published_at": date_match.group(0) if date_match else "",
                "topic": _classify_topic(title),
                "snippet": context[:300].strip(),
            }
        )

    for match in link_pattern.finditer(markdown):
        title = match.group(1).strip()
        href = match.group(2)
        if len(title) < 15 or len(title) > 200:
            continue
        if any(a["title"] == title for a in articles):
            continue
        if href.startswith("/"):
            href = urljoin(base_url, href)
        if not href.startswith("http"):
            continue

        context_start = max(0, match.start() - 100)
        context_end = min(len(markdown), match.end() + 200)
        context = markdown[context_start:context_end]
        date_match = _DATE_PATTERN.search(context)

        articles.append(
            {
                "title": title,
                "url": href,
                "published_at": date_match.group(0) if date_match else "",
                "topic": _classify_topic(title),
                "snippet": context[:300].strip(),
            }
        )

    return articles[:20]


async def run_news(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    base = _base_url(req)
    company = _company_name(req)
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")

    source = None
    all_markdown = ""
    news_url = ""

    for path in _NEWS_PATHS:
        url = urljoin(base + "/", path.lstrip("/"))
        resp = await safe_scrape(crawler, url)
        if resp:
            source = evidence_from_scrape(url, resp)
            news_url = url
            all_markdown = resp.markdown
            break

    if not source:
        return []

    articles = _extract_articles(all_markdown, company, base)
    if not articles:
        return [
            NewsSignalRecord(
                objectID=f"news_{slug}_page",
                company=company,
                title=f"{company} newsroom",
                url=news_url,
                topic="company_news",
                source_url=news_url,
                confidence=0.5,
                citations=[
                    make_citation(
                        source, "url", news_url, "Newsroom page found but no articles extracted"
                    )
                ],
            ).model_dump(mode="json")
        ]

    records: list[dict] = []
    for i, article in enumerate(articles):
        art_slug = re.sub(r"[^a-z0-9]+", "_", article["title"].lower())[:40].strip("_")
        records.append(
            NewsSignalRecord(
                objectID=f"news_{slug}_{art_slug}_{i}",
                company=company,
                title=article["title"],
                url=article["url"],
                topic=article["topic"],
                published_at=article.get("published_at", ""),
                summary=article.get("snippet", ""),
                source_url=news_url,
                confidence=0.7,
                citations=[
                    make_citation(
                        source,
                        "title",
                        article["title"],
                        article.get("snippet", "")[:200],
                    )
                ],
            ).model_dump(mode="json")
        )

    return records
