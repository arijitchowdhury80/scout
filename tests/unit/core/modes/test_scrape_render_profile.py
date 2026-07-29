"""Intelligence-render knobs: the moat depends on the RIGHT page being FULLY
rendered before extraction. ScrapeRequest gains scan_full_page / wait_until /
delay_before_return_html / block_images, which must map onto the matching
Crawl4AI 0.7.7 CrawlerRunConfig params (read receipt 2026-07-27, crawl4ai
0.7.7: scan_full_page, wait_until, delay_before_return_html, exclude_all_images,
exclude_external_images all present). Defaults must stay inert so every existing
caller renders exactly as before.
"""

from scout.core.modes.scrape import _build_run_config
from scout.core.types import ScrapeRequest


def test_render_defaults_are_inert() -> None:
    """New knobs default to crawl4ai's own defaults — existing callers unchanged."""
    req = ScrapeRequest(url="https://example.com")
    rc = _build_run_config(req, want_screenshot=False)
    assert rc.scan_full_page is False
    # empty wait_until must NOT override crawl4ai's sane default of domcontentloaded
    assert rc.wait_until == "domcontentloaded"
    assert rc.delay_before_return_html == 0.1  # crawl4ai default, untouched
    assert rc.exclude_all_images is False
    assert rc.exclude_external_images is False


def test_scan_full_page_maps_through() -> None:
    req = ScrapeRequest(url="https://x.com", scan_full_page=True)
    rc = _build_run_config(req, want_screenshot=False)
    assert rc.scan_full_page is True


def test_wait_until_override_when_set() -> None:
    req = ScrapeRequest(url="https://x.com", wait_until="networkidle")
    rc = _build_run_config(req, want_screenshot=False)
    assert rc.wait_until == "networkidle"


def test_empty_wait_until_keeps_crawl4ai_default() -> None:
    req = ScrapeRequest(url="https://x.com", wait_until="")
    rc = _build_run_config(req, want_screenshot=False)
    assert rc.wait_until == "domcontentloaded"


def test_delay_before_return_html_override_when_set() -> None:
    req = ScrapeRequest(url="https://x.com", delay_before_return_html=2.5)
    rc = _build_run_config(req, want_screenshot=False)
    assert rc.delay_before_return_html == 2.5


def test_none_delay_keeps_crawl4ai_default() -> None:
    req = ScrapeRequest(url="https://x.com", delay_before_return_html=None)
    rc = _build_run_config(req, want_screenshot=False)
    assert rc.delay_before_return_html == 0.1


def test_block_images_excludes_all_and_external_images() -> None:
    req = ScrapeRequest(url="https://x.com", block_images=True)
    rc = _build_run_config(req, want_screenshot=False)
    assert rc.exclude_all_images is True
    assert rc.exclude_external_images is True


def test_intelligence_profile_combination() -> None:
    """The exec/product runners will request this exact shape."""
    req = ScrapeRequest(
        url="https://x.com",
        use_js=True,
        scan_full_page=True,
        wait_until="domcontentloaded",
        delay_before_return_html=2.0,
        block_images=True,
    )
    rc = _build_run_config(req, want_screenshot=False)
    assert rc.scan_full_page is True
    assert rc.wait_until == "domcontentloaded"
    assert rc.delay_before_return_html == 2.0
    assert rc.exclude_all_images is True
