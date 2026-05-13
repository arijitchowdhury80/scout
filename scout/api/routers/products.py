"""Products router — product catalog crawl to Algolia-ready records."""

from fastapi import APIRouter, Depends

from scout.api.deps import get_crawler
from scout.core.crawler import ScoutCrawler
from scout.core.types import ProductCrawlRequest, ProductCrawlResponse

router = APIRouter()


@router.post("/products", response_model=ProductCrawlResponse)
async def products(
    req: ProductCrawlRequest,
    crawler: ScoutCrawler = Depends(get_crawler),
) -> ProductCrawlResponse:
    """Discover product pages and return normalized Algolia records."""
    return await crawler.products(req)
