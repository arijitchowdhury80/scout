"""LLM extraction fallback gating for the company runner's executives.

The 3-tier heuristic (JSON-LD Person nodes, team cards, regex-on-markdown)
is tried first. The LLM fallback (scout.core.llm_extract.llm_extract_executives)
must fire ONLY when that heuristic found zero executives AND the crawler
exposes a usable fallback_llm_api_key. These tests always mock the LLM call.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scout.core.enrich.wikidata import WikidataExec
from scout.core.llm_extract import LLMExecutiveItem
from scout.core.platform.types import RunRequest
from scout.core.types import ScoutMetadata, ScrapeResponse
from scout.core.use_cases.runners.company import run_company


@pytest.mark.asyncio
async def test_wikidata_enrichment_adds_missing_execs_when_enabled() -> None:
    """Waterfall source #2: on-site found nothing, Wikidata fills the gap."""
    crawler = _mock_crawler(
        {"acme.com": _scrape_ok("https://www.acme.com", "# Acme\n\nNo leadership here.\n")},
        llm_api_key="",
    )
    crawler.enrichment_enabled = True
    with patch(
        "scout.core.use_cases.runners.company.wikidata_executives",
        new_callable=AsyncMock,
        return_value=[WikidataExec(name="Jane Park", title="CEO", qid="Q1", company_qid="Q2")],
    ) as mock_wd:
        records = await run_company(_req(), crawler)
    mock_wd.assert_called_once()
    execs = [r for r in records if r.get("record_type") == "executive"]
    assert any(r["name"] == "Jane Park" and r["title"] == "CEO" for r in execs)


@pytest.mark.asyncio
async def test_wikidata_enrichment_skipped_when_crawler_not_enrichment_enabled() -> None:
    """A bare MagicMock (unset enrichment_enabled) must NOT fire a live call."""
    crawler = _mock_crawler(
        {"acme.com": _scrape_ok("https://www.acme.com", "# Acme\n\nNo leadership here.\n")},
        llm_api_key="",
    )  # enrichment_enabled left unset -> child Mock, not `is True`
    with patch(
        "scout.core.use_cases.runners.company.wikidata_executives", new_callable=AsyncMock
    ) as mock_wd:
        await run_company(_req(), crawler)
    mock_wd.assert_not_called()


@pytest.mark.asyncio
async def test_wikidata_does_not_duplicate_onsite_execs() -> None:
    """A name already found on-site is not re-added by Wikidata (dedup)."""
    html = '<script type="application/ld+json">{"@type":"Person","name":"Jane Doe","jobTitle":"CEO"}</script>'
    crawler = _mock_crawler(
        {"acme.com": _scrape_ok("https://www.acme.com", "# Acme\n", raw_html=html)},
        llm_api_key="",
    )
    crawler.enrichment_enabled = True
    with patch(
        "scout.core.use_cases.runners.company.wikidata_executives",
        new_callable=AsyncMock,
        return_value=[WikidataExec(name="Jane Doe", title="Founder", qid="Q1", company_qid="Q2")],
    ):
        records = await run_company(_req(), crawler)
    janes = [r for r in records if r.get("record_type") == "executive" and r["name"] == "Jane Doe"]
    assert len(janes) == 1  # on-site record kept, Wikidata dup dropped
    assert janes[0]["title"] == "CEO"  # the on-site title, not Wikidata's "Founder"


def _meta(url: str = "https://acme.com") -> ScoutMetadata:
    return ScoutMetadata(url=url, crawled_at="2026-07-27T00:00:00Z")


def _scrape_ok(url: str, markdown: str, raw_html: str = "") -> ScrapeResponse:
    return ScrapeResponse(
        success=True,
        url=url,
        markdown=markdown,
        raw_html=raw_html,
        metadata=_meta(url),
        duration_ms=10,
    )


def _scrape_fail(url: str) -> ScrapeResponse:
    return ScrapeResponse(
        success=False, url=url, markdown="", metadata=_meta(url), duration_ms=5, error="404"
    )


def _mock_crawler(responses: dict[str, ScrapeResponse], *, llm_api_key: str = "") -> MagicMock:
    crawler = MagicMock()

    async def _scrape(req):
        for pattern, resp in responses.items():
            if pattern in req.url:
                return resp
        return _scrape_fail(req.url)

    crawler.scrape = AsyncMock(side_effect=_scrape)
    crawler.fallback_llm_api_key = llm_api_key
    return crawler


def _req() -> RunRequest:
    return RunRequest(
        use_case="company", query="Acme Corp", url="https://www.acme.com", mode="auto"
    )


@pytest.mark.asyncio
async def test_llm_fallback_not_called_when_heuristics_found_executives() -> None:
    """JSON-LD Person node already gives us an exec -> LLM must never run."""
    html_with_person = """
    <script type="application/ld+json">
    {"@type": "Person", "name": "Jane Doe", "jobTitle": "CEO"}
    </script>
    """
    crawler = _mock_crawler(
        {
            "acme.com": _scrape_ok(
                "https://www.acme.com",
                "# Acme Corp\n\nWe build things.\n",
                raw_html=html_with_person,
            ),
        },
        llm_api_key="fake-anthropic-key",
    )

    with patch(
        "scout.core.use_cases.runners.company.llm_extract_executives", new_callable=AsyncMock
    ) as mock_llm:
        records = await run_company(_req(), crawler)

    mock_llm.assert_not_called()
    exec_records = [r for r in records if r.get("record_type") == "executive"]
    assert len(exec_records) == 1
    assert exec_records[0]["name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_llm_fallback_called_when_heuristics_empty_and_llm_enabled() -> None:
    """No JSON-LD/team-card/regex signal at all -> LLM fallback fires and its output is used."""
    crawler = _mock_crawler(
        {
            "acme.com": _scrape_ok(
                "https://www.acme.com",
                "# Acme Corp\n\nWe build things. No leadership markup here at all.\n",
            ),
        },
        llm_api_key="fake-anthropic-key",
    )

    with patch(
        "scout.core.use_cases.runners.company.llm_extract_executives",
        new_callable=AsyncMock,
        return_value=[LLMExecutiveItem(name="Sam Rivera", title="Founder")],
    ) as mock_llm:
        records = await run_company(_req(), crawler)

    mock_llm.assert_called_once()
    exec_records = [r for r in records if r.get("record_type") == "executive"]
    assert len(exec_records) == 1
    assert exec_records[0]["name"] == "Sam Rivera"
    assert exec_records[0]["title"] == "Founder"


@pytest.mark.asyncio
async def test_llm_fallback_never_called_when_llm_disabled() -> None:
    """No fallback_llm_api_key on the crawler -> LLM must never run, even with zero heuristic hits."""
    crawler = _mock_crawler(
        {
            "acme.com": _scrape_ok(
                "https://www.acme.com",
                "# Acme Corp\n\nWe build things. No leadership markup here at all.\n",
            ),
        },
        llm_api_key="",
    )

    with patch(
        "scout.core.use_cases.runners.company.llm_extract_executives", new_callable=AsyncMock
    ) as mock_llm:
        records = await run_company(_req(), crawler)

    mock_llm.assert_not_called()
    exec_records = [r for r in records if r.get("record_type") == "executive"]
    assert exec_records == []


@pytest.mark.asyncio
async def test_llm_fallback_not_called_when_crawler_has_no_key_attribute() -> None:
    """A bare MagicMock (as used by every pre-existing runner test) must not look like a key.

    Accessing an unset attribute on a MagicMock returns another Mock, which is
    truthy but not a string. Guard against that so old tests that never set
    fallback_llm_api_key don't accidentally trigger a real LLM call.
    """
    crawler = MagicMock()
    crawler.scrape = AsyncMock(
        return_value=_scrape_ok(
            "https://www.acme.com",
            "# Acme Corp\n\nWe build things. No leadership markup here at all.\n",
        )
    )
    # Deliberately do NOT set crawler.fallback_llm_api_key.

    with patch(
        "scout.core.use_cases.runners.company.llm_extract_executives", new_callable=AsyncMock
    ) as mock_llm:
        await run_company(_req(), crawler)

    mock_llm.assert_not_called()
