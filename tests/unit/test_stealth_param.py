from scout.core.types import ScrapeRequest, MapRequest, CrawlRequest


def test_scrape_request_stealth_default_false():
    req = ScrapeRequest(url="https://example.com")
    assert not req.stealth


def test_scrape_request_stealth_true():
    req = ScrapeRequest(url="https://example.com", stealth=True)
    assert req.stealth


def test_map_request_stealth_default_false():
    req = MapRequest(url="https://example.com")
    assert not req.stealth


def test_crawl_request_stealth_default_false():
    req = CrawlRequest(url="https://example.com")
    assert not req.stealth
