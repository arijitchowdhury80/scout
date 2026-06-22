"""crawl-from-here: after a human clears a site, Scout discovers detail-page
links on the cleared page and visits each in the SAME authenticated session,
extracting markdown + JSON-LD per page. Pure helpers are tested directly; the
crawl flow uses a fake navigate-bridge + injected sleep (no real browser).
"""

import asyncio

from scout.core.crawl_from_here import (
    CrawlFromHereResult,
    crawl_from_here,
    extract_detail_links,
    extract_jsonld,
)

_BASE = "https://www.zillow.com/roswell-ga/rentals/"

_LIST_HTML = """
<a href="/homedetails/301-River/123_zpid/">A</a>
<a href="/homedetails/302-Glen/124_zpid/">B</a>
<a href="https://www.zillow.com/homedetails/303/125_zpid/">C</a>
<a href="/about/">about</a>
<a href="https://other.com/homedetails/x/">ext</a>
<a href="mailto:x@y.com">mail</a>
<a href="#top">frag</a>
<a href="/homedetails/301-River/123_zpid/">dup</a>
"""


def _run(coro):
    return asyncio.run(coro)


def test_extract_detail_links_filters_dedups_and_resolves() -> None:
    links = extract_detail_links(_LIST_HTML, _BASE, contains="/homedetails/", limit=5)
    assert links == [
        "https://www.zillow.com/homedetails/301-River/123_zpid/",
        "https://www.zillow.com/homedetails/302-Glen/124_zpid/",
        "https://www.zillow.com/homedetails/303/125_zpid/",
    ]


def test_extract_detail_links_excludes_offsite_and_junk_without_filter() -> None:
    links = extract_detail_links(_LIST_HTML, _BASE, contains="", limit=10)
    assert "https://other.com/homedetails/x/" not in links
    assert all(not link.startswith("mailto:") for link in links)
    assert all("#" not in link for link in links)


def test_extract_detail_links_respects_limit() -> None:
    assert len(extract_detail_links(_LIST_HTML, _BASE, contains="/homedetails/", limit=2)) == 2


def test_extract_jsonld_parses_objects_and_graph() -> None:
    html = (
        '<script type="application/ld+json">{"@type":"RealEstateListing","name":"X"}</script>'
        '<script type="application/ld+json">{"@graph":[{"@type":"Place"},{"@type":"Event"}]}</script>'
        '<script type="application/ld+json">{bad json}</script>'
    )
    out = extract_jsonld(html)
    types = [o.get("@type") for o in out]
    assert "RealEstateListing" in types
    assert "Place" in types and "Event" in types  # @graph flattened
    # malformed block is skipped, not fatal


class FakeCapture:
    def __init__(self, *, url, title="", html="", text=""):
        self.url, self.title, self.html, self.text = url, title, html, text


class FakeNavBridge:
    def __init__(self, mapping):
        self._mapping = mapping
        self.visited = []

    async def navigate_capture(self, url):
        self.visited.append(url)
        return self._mapping[url]


async def _noop_sleep(_s):
    return None


def test_crawl_from_here_visits_each_link_and_extracts() -> None:
    a = "https://www.zillow.com/homedetails/301-River/123_zpid/"
    b = "https://www.zillow.com/homedetails/302-Glen/124_zpid/"
    bridge = FakeNavBridge(
        {
            a: FakeCapture(
                url=a,
                title="301 River Glen Dr",
                html='<script type="application/ld+json">{"@type":"RealEstateListing","name":"301 River"}</script>',
                text="x" * 300,
            ),
            b: FakeCapture(url=b, title="Just a moment...", html="press & hold", text="blocked"),
        }
    )
    result = _run(
        crawl_from_here(
            _LIST_HTML, _BASE, bridge, sleep=_noop_sleep, contains="/homedetails/", limit=2
        )
    )
    assert isinstance(result, CrawlFromHereResult)
    assert result.discovered == 2
    assert result.crawled == 2
    assert result.blocked == 1
    assert bridge.visited == [a, b]
    rec_a = next(r for r in result.records if r.url == a)
    assert rec_a.jsonld and rec_a.jsonld[0]["@type"] == "RealEstateListing"
    assert rec_a.blocked is False
    rec_b = next(r for r in result.records if r.url == b)
    assert rec_b.blocked is True
    assert rec_b.vendor in ("perimeterx", "cloudflare")


def test_crawl_from_here_records_navigation_errors_without_crashing() -> None:
    class BoomBridge:
        visited = []

        async def navigate_capture(self, url):
            raise RuntimeError("nav failed")

    result = _run(
        crawl_from_here(
            '<a href="/homedetails/301-River/123_zpid/">A</a>',
            _BASE,
            BoomBridge(),
            sleep=_noop_sleep,
            contains="/homedetails/",
            limit=1,
        )
    )
    assert result.crawled == 1
    assert "nav failed" in result.records[0].error
