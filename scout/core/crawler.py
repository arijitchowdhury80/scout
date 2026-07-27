"""ScoutCrawler — unified entry point routing requests to the appropriate mode."""

from scout.core.modes.crawl import crawl as _crawl
from scout.core.modes.extract import extract as _extract
from scout.core.modes.map import map_urls as _map_urls
from scout.core.modes.products import products as _products
from scout.core.modes.scrape import scrape as _scrape
from scout.core.modes.screenshot import screenshot as _screenshot
from scout.core.types import (
    CrawlRequest,
    CrawlResponse,
    ExtractRequest,
    ExtractResponse,
    MapRequest,
    MapResponse,
    ProductCrawlRequest,
    ProductCrawlResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScreenshotRequest,
    ScreenshotResponse,
)


class ScoutCrawler:
    def __init__(self, llm_api_key: str = "", llm_extraction_fallback_enabled: bool = True) -> None:
        """Initialise ScoutCrawler.

        `llm_api_key` is required for extract mode, and also gates the LLM
        extraction fallback (products/executives) unless that fallback is
        separately disabled via `llm_extraction_fallback_enabled` — see
        `fallback_llm_api_key` below and scout/api/config.py's
        `llm_extraction_fallback_enabled` setting.
        """
        self.llm_api_key = llm_api_key
        self.llm_extraction_fallback_enabled = llm_extraction_fallback_enabled

    @property
    def fallback_llm_api_key(self) -> str:
        """Effective API key for the LLM extraction fallback (products/executives).

        Empty whenever the fallback is disabled or no key is configured.
        Deliberately separate from `llm_api_key` so disabling the fallback
        (cost control) never disables the primary `extract()` mode, and vice
        versa.
        """
        return self.llm_api_key if self.llm_extraction_fallback_enabled else ""

    async def scrape(self, req: ScrapeRequest) -> ScrapeResponse:
        """Fetch a single URL and return clean markdown content."""
        return await _scrape(req)

    async def crawl(self, req: CrawlRequest) -> CrawlResponse:
        """Recursively crawl a site via BFS and return all pages."""
        return await _crawl(req)

    async def extract(self, req: ExtractRequest) -> ExtractResponse:
        """Crawl a URL and extract structured data using an LLM strategy."""
        return await _extract(req, self.llm_api_key)

    async def map_urls(self, req: MapRequest) -> MapResponse:
        """Discover all URLs on a site without extracting page content."""
        return await _map_urls(req)

    async def screenshot(self, req: ScreenshotRequest) -> ScreenshotResponse:
        """Capture a visual screenshot of a URL as a base64-encoded PNG."""
        return await _screenshot(req)

    async def products(self, req: ProductCrawlRequest) -> ProductCrawlResponse:
        """Crawl product pages and prepare Algolia-ready records."""
        return await _products(req, llm_api_key=self.fallback_llm_api_key)
