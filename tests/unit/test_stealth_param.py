import pytest
from scout.core.types import ScrapeRequest, MapRequest, CrawlRequest


def test_scrape_request_stealth_default_false():
    req = ScrapeRequest(url="https://example.com")
    assert req.stealth == False


def test_scrape_request_stealth_true():
    req = ScrapeRequest(url="https://example.com", stealth=True)
    assert req.stealth == True


def test_map_request_stealth_default_false():
    req = MapRequest(url="https://example.com")
    assert req.stealth == False


def test_crawl_request_stealth_default_false():
    req = CrawlRequest(url="https://example.com")
    assert req.stealth == False
