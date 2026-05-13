"""Product catalog crawl mode — prepares Algolia-ready product records."""

from __future__ import annotations

import time
from urllib.parse import urlparse

import structlog

from scout.core.artifacts import write_product_artifacts
from scout.core.modes.map import map_urls
from scout.core.modes.scrape import scrape
from scout.core.products.algolia import build_algolia_record
from scout.core.products.discovery import ProductUrlGroups, group_product_urls, normalize_start_url
from scout.core.products.discovery import extract_product_links, select_category_urls
from scout.core.products.jsonld import extract_product_jsonld
from scout.core.types import (
    AlgoliaProductRecord,
    MapRequest,
    ProductArtifactFiles,
    ProductCrawlRequest,
    ProductCrawlResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScoutFormats,
)

logger = structlog.get_logger(__name__)


async def products(req: ProductCrawlRequest) -> ProductCrawlResponse:
    """Discover product pages, extract product fields, and emit Algolia records."""
    started = time.monotonic()
    start_url = normalize_start_url(req.site, req.start_url)
    if not start_url:
        return _error(req, "Product crawl requires site or start_url.", started)

    try:
        groups = []
        if _has_path(start_url):
            groups = await _discover_from_categories(req, [start_url])
        if groups:
            mapped_urls = [start_url]
        else:
            map_pages = 100 if _has_path(start_url) else max(500, req.max_products * 20)
            mapped = await map_urls(MapRequest(url=start_url, max_pages=map_pages))
            if not mapped.success:
                return _error(req, mapped.error or "URL discovery failed.", started, start_url)
            mapped_urls = mapped.urls
            groups = group_product_urls(
                mapped.urls,
                max_categories=req.max_categories,
                limit_per_category=req.limit_per_category,
            )
            if not groups:
                groups = await _discover_from_categories(req, [start_url, *mapped.urls])
        records: list[AlgoliaProductRecord] = []
        raw_products: list[dict] = []

        for group in groups:
            for url in group.product_urls:
                if len(records) >= req.max_products:
                    break
                scrape_resp = await scrape(
                    ScrapeRequest(
                        url=url,
                        formats=[ScoutFormats.MARKDOWN, ScoutFormats.RAW_HTML],
                        use_js=req.use_js,
                        timeout_ms=req.timeout_ms,
                        stealth=req.stealth,
                    )
                )
                if not scrape_resp.success:
                    logger.warning(
                        "[scout/products] scrape failed", url=url, error=scrape_resp.error
                    )
                    continue
                if _is_blocked(scrape_resp):
                    logger.warning("[scout/products] blocked page skipped", url=url)
                    continue
                product = extract_product_jsonld(scrape_resp.raw_html)
                record = build_algolia_record(
                    url=scrape_resp.url,
                    title=scrape_resp.metadata.title,
                    category_name=group.category_name,
                    category_url=group.category_url,
                    product=product,
                )
                records.append(record)
                raw_products.append(record.model_dump(mode="json", by_alias=True))

        categories = [group.category_name for group in groups]
        duration_ms = int((time.monotonic() - started) * 1000)
        files = ProductArtifactFiles()
        output_dir = ""
        if req.persist or req.output_dir:
            files = write_product_artifacts(
                req=req,
                records=records,
                categories=categories,
                discovered_urls=mapped_urls,
                raw_products=raw_products,
                duration_ms=duration_ms,
            )
            output_dir = req.output_dir or str(files.manifest).rsplit("/", 1)[0]

        return ProductCrawlResponse(
            success=True,
            query=req.query,
            site=req.site,
            start_url=start_url,
            output_dir=output_dir,
            records=records,
            total_records=len(records),
            categories=categories,
            files=files,
            duration_ms=duration_ms,
        )

    except Exception as exc:
        logger.exception("[scout/products] error", query=req.query, site=req.site, exc=str(exc))
        return _error(req, str(exc), started, start_url)


def _error(
    req: ProductCrawlRequest,
    message: str,
    started: float,
    start_url: str = "",
) -> ProductCrawlResponse:
    duration_ms = int((time.monotonic() - started) * 1000)
    return ProductCrawlResponse(
        success=False,
        query=req.query,
        site=req.site,
        start_url=start_url,
        records=[],
        total_records=0,
        error=message,
        duration_ms=duration_ms,
    )


def _has_path(url: str) -> bool:
    return bool(urlparse(url).path.strip("/"))


def _is_blocked(resp: ScrapeResponse) -> bool:
    text = f"{resp.metadata.title} {resp.markdown}".lower()
    return "access denied" in text or "powered and protected by" in text


async def _discover_from_categories(
    req: ProductCrawlRequest,
    urls: list[str],
) -> list[ProductUrlGroups]:
    category_urls = select_category_urls(urls, query=req.query, limit=req.max_categories)
    groups = []
    for category_url in category_urls:
        scrape_resp = await scrape(
            ScrapeRequest(
                url=category_url,
                formats=[ScoutFormats.MARKDOWN],
                use_js=req.use_js,
                timeout_ms=req.timeout_ms,
                stealth=req.stealth,
            )
        )
        if not scrape_resp.success:
            continue
        product_urls = extract_product_links(
            category_url,
            scrape_resp.links,
            limit=req.limit_per_category,
        )
        if not product_urls:
            continue
        groups.append(
            ProductUrlGroups(
                category_url=category_url,
                category_name=category_url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").title(),
                product_urls=product_urls,
            )
        )
    return groups
