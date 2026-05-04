"""ScoutCrawler — unified entry point routing requests to the appropriate mode."""
from scout.core.modes.crawl import crawl as _crawl
from scout.core.modes.extract import extract as _extract
from scout.core.modes.map import map_urls as _map_urls
from scout.core.modes.scrape import scrape as _scrape
from scout.core.modes.screenshot import screenshot as _screenshot
from scout.core.types import (
    CrawlRequest,
    CrawlResponse,
    ExtractRequest,
    ExtractResponse,
    MapRequest,
    MapResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScreenshotRequest,
    ScreenshotResponse,
)


class ScoutCrawler:
    def __init__(self, llm_api_key: str = "") -> None:
        self.llm_api_key = llm_api_key

    async def scrape(self, req: ScrapeRequest) -> ScrapeResponse:
        return await _scrape(req)

    async def crawl(self, req: CrawlRequest) -> CrawlResponse:
        return await _crawl(req)

    async def extract(self, req: ExtractRequest) -> ExtractResponse:
        return await _extract(req, self.llm_api_key)

    async def map_urls(self, req: MapRequest) -> MapResponse:
        return await _map_urls(req)

    async def screenshot(self, req: ScreenshotRequest) -> ScreenshotResponse:
        return await _screenshot(req)
