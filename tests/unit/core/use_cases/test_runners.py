"""Tests for intelligence vertical runners — mock ScoutCrawler.scrape()."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from scout.core.platform.types import RunRequest
from scout.core.types import ScoutMetadata, ScrapeResponse


def _meta(url: str = "https://example.com") -> ScoutMetadata:
    return ScoutMetadata(url=url, crawled_at="2026-06-22T00:00:00Z")


def _scrape_ok(url: str, markdown: str, links: list[str] | None = None) -> ScrapeResponse:
    return ScrapeResponse(
        success=True,
        url=url,
        markdown=markdown,
        links=links or [],
        metadata=_meta(url),
        duration_ms=100,
    )


def _scrape_fail(url: str) -> ScrapeResponse:
    return ScrapeResponse(
        success=False,
        url=url,
        markdown="",
        metadata=_meta(url),
        error="404 Not Found",
        duration_ms=50,
    )


def _mock_crawler(responses: dict[str, ScrapeResponse]) -> MagicMock:
    crawler = MagicMock()

    async def _scrape(req):
        for pattern, resp in responses.items():
            if pattern in req.url:
                return resp
        return _scrape_fail(req.url)

    crawler.scrape = AsyncMock(side_effect=_scrape)
    return crawler


def _mock_exact_crawler(responses: dict[str, ScrapeResponse]) -> MagicMock:
    crawler = MagicMock()

    async def _scrape(req):
        return responses.get(req.url, _scrape_fail(req.url))

    crawler.scrape = AsyncMock(side_effect=_scrape)
    return crawler


def _req(use_case: str, query: str = "Acme Corp", url: str = "https://www.acme.com") -> RunRequest:
    return RunRequest(use_case=use_case, query=query, url=url, mode="auto")


# ---------------------------------------------------------------------------
# Company runner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_company_runner_extracts_company_record() -> None:
    from scout.core.use_cases.runners.company import run_company

    crawler = _mock_crawler(
        {
            "acme.com": _scrape_ok(
                "https://www.acme.com",
                "# Acme Corp\n\nWe build great products for the web.\n"
                "Follow us on https://www.linkedin.com/company/acme\n"
                "and https://twitter.com/acme\n",
                links=["https://www.linkedin.com/company/acme", "https://twitter.com/acme"],
            ),
        }
    )

    records = await run_company(_req("company"), crawler)

    assert len(records) >= 1
    company_rec = records[0]
    assert company_rec["record_type"] == "company"
    assert company_rec["name"] == "Acme Corp"
    assert company_rec["website"] == "https://www.acme.com"
    assert company_rec["confidence"] > 0
    assert company_rec["citations"]

    social_recs = [r for r in records if r["record_type"] == "company_social"]
    platforms = {r["platform"] for r in social_recs}
    assert "linkedin" in platforms
    assert "twitter" in platforms


@pytest.mark.asyncio
async def test_company_runner_extracts_executives() -> None:
    from scout.core.use_cases.runners.company import run_company

    crawler = _mock_crawler(
        {
            "acme.com": _scrape_ok(
                "https://www.acme.com",
                "# Acme Corp\n\n"
                "## Leadership\n\n"
                "**Jane Smith** — Chief Executive Officer\n\n"
                "**John Doe**, VP of Engineering\n",
            ),
        }
    )

    records = await run_company(_req("company"), crawler)

    exec_recs = [r for r in records if r["record_type"] == "executive"]
    assert len(exec_recs) >= 1
    names = {r["name"] for r in exec_recs}
    assert "Jane Smith" in names


@pytest.mark.asyncio
async def test_company_runner_returns_empty_on_total_failure() -> None:
    from scout.core.use_cases.runners.company import run_company

    crawler = _mock_crawler({})
    records = await run_company(_req("company"), crawler)
    assert records == []


@pytest.mark.asyncio
async def test_company_runner_stops_after_first_about_and_team_success() -> None:
    from scout.core.use_cases.runners.company import run_company

    crawler = _mock_crawler(
        {
            "acme.com/about": _scrape_ok(
                "https://www.acme.com/about",
                "# About Acme\n\nAcme builds AI search tools.",
            ),
            "acme.com/team": _scrape_ok(
                "https://www.acme.com/team",
                "# Team\n\n**Jane Smith** — Chief Executive Officer",
            ),
        }
    )

    records = await run_company(_req("company"), crawler)
    requested_urls = [call.args[0].url for call in crawler.scrape.await_args_list]

    assert records
    assert "https://www.acme.com/about" in requested_urls
    assert "https://www.acme.com/about-us" not in requested_urls
    assert "https://www.acme.com/team" in requested_urls
    assert "https://www.acme.com/leadership" not in requested_urls


# ---------------------------------------------------------------------------
# Careers runner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_careers_runner_detects_ats_and_departments() -> None:
    from scout.core.use_cases.runners.careers import run_careers

    crawler = _mock_crawler(
        {
            "/careers": _scrape_ok(
                "https://www.acme.com/careers",
                "# Join Acme\n\n"
                "We use Greenhouse to manage applications.\n"
                "Open positions in engineering, product, and design.\n"
                "Apply at boards.greenhouse.io/acme\n"
                "Senior Software Engineer - Backend\n"
                "Product Designer - Mobile\n",
                links=["https://boards.greenhouse.io/acme/jobs/123"],
            ),
        }
    )

    records = await run_careers(_req("careers"), crawler)

    assert len(records) == 1
    rec = records[0]
    assert rec["record_type"] == "career_site"
    assert rec["ats_platform"] == "greenhouse"
    assert "engineering" in rec["departments"]
    assert "product" in rec["departments"]
    assert rec["confidence"] > 0.5


@pytest.mark.asyncio
async def test_careers_runner_returns_empty_when_no_careers_page() -> None:
    from scout.core.use_cases.runners.careers import run_careers

    crawler = _mock_crawler({})
    records = await run_careers(_req("careers"), crawler)
    assert records == []


@pytest.mark.asyncio
async def test_careers_runner_uses_supplied_exact_careers_url_first() -> None:
    from scout.core.use_cases.runners.careers import run_careers

    exact_url = "https://www.adobe.com/careers.html"
    crawler = _mock_exact_crawler(
        {
            exact_url: _scrape_ok(
                exact_url,
                "# Careers\n\nEngineering, sales, support, and design roles.",
            )
        }
    )

    records = await run_careers(_req("careers", query="Adobe", url=exact_url), crawler)

    assert len(records) == 1
    assert records[0]["careers_url"] == exact_url
    assert crawler.scrape.await_args_list[0].args[0].url == exact_url


# ---------------------------------------------------------------------------
# Investor runner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_investor_runner_detects_ticker_and_filings() -> None:
    from scout.core.use_cases.runners.investor import run_investor

    crawler = _mock_crawler(
        {
            "/investor": _scrape_ok(
                "https://www.acme.com/investors",
                "# Investor Relations\n\n"
                "NASDAQ: ACME\n\n"
                "## Resources\n"
                "- Annual Report 2025\n"
                "- Quarterly Report Q4 2025\n"
                "- Earnings Call Transcript\n"
                "- SEC Filing DEF 14A\n",
            ),
        }
    )

    records = await run_investor(_req("investor"), crawler)

    assert len(records) >= 2
    ir_page = records[0]
    assert ir_page["record_type"] == "investor_asset"
    assert ir_page["asset_type"] == "investor_page"
    assert "ACME" in ir_page["title"]

    asset_types = {r["asset_type"] for r in records}
    assert "annual_report" in asset_types
    assert "quarterly_report" in asset_types
    assert "earnings" in asset_types


@pytest.mark.asyncio
async def test_investor_runner_returns_empty_when_no_ir_page() -> None:
    from scout.core.use_cases.runners.investor import run_investor

    crawler = _mock_crawler({})
    records = await run_investor(_req("investor"), crawler)
    assert records == []


@pytest.mark.asyncio
async def test_investor_runner_uses_supplied_exact_investor_url_first() -> None:
    from scout.core.use_cases.runners.investor import run_investor

    exact_url = "https://www.adobe.com/investor-relations.html"
    crawler = _mock_exact_crawler(
        {
            exact_url: _scrape_ok(
                exact_url,
                "# Investor Relations\n\nAnnual Report 2025. Earnings release. NASDAQ: ADBE.",
            )
        }
    )

    records = await run_investor(_req("investor", query="Adobe", url=exact_url), crawler)

    assert len(records) >= 2
    assert records[0]["url"] == exact_url
    assert crawler.scrape.await_args_list[0].args[0].url == exact_url


# ---------------------------------------------------------------------------
# News runner
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_news_runner_extracts_articles() -> None:
    from scout.core.use_cases.runners.news import run_news

    crawler = _mock_crawler(
        {
            "/news": _scrape_ok(
                "https://www.acme.com/news",
                "# Acme Newsroom\n\n"
                "## Acme Launches Revolutionary AI Platform\n"
                "January 15, 2026\n\n"
                "We are excited to announce our new platform.\n\n"
                "## Acme Partners with Microsoft for Enterprise AI\n"
                "February 1, 2026\n\n"
                "Strategic partnership to bring AI to the enterprise.\n\n"
                "## Acme Raises $100M Series D Funding Round\n"
                "March 10, 2026\n\n",
            ),
        }
    )

    records = await run_news(_req("news"), crawler)

    assert len(records) >= 2
    assert all(r["record_type"] == "news_signal" for r in records)
    topics = {r["topic"] for r in records}
    assert "product_launch" in topics or "partnership" in topics or "funding" in topics
    assert records[0]["company"] == "Acme Corp"


@pytest.mark.asyncio
async def test_news_runner_returns_fallback_when_no_articles_parsed() -> None:
    from scout.core.use_cases.runners.news import run_news

    crawler = _mock_crawler(
        {
            "/news": _scrape_ok(
                "https://www.acme.com/news",
                "Welcome to our newsroom. Check back soon for updates.",
            ),
        }
    )

    records = await run_news(_req("news"), crawler)

    assert len(records) == 1
    assert records[0]["record_type"] == "news_signal"
    assert "newsroom" in records[0]["title"].lower()


@pytest.mark.asyncio
async def test_news_runner_returns_empty_when_no_news_page() -> None:
    from scout.core.use_cases.runners.news import run_news

    crawler = _mock_crawler({})
    records = await run_news(_req("news"), crawler)
    assert records == []


# ---------------------------------------------------------------------------
# Dispatcher integration — real runners via mock crawler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dispatcher_uses_real_runner_for_company_in_auto_mode(tmp_path) -> None:
    from scout.core.platform.run import run_use_case

    crawler = _mock_crawler(
        {
            "acme.com": _scrape_ok(
                "https://www.acme.com",
                "# Acme Corp\nBuilding the future.",
            ),
        }
    )

    resp = await run_use_case(
        RunRequest(
            use_case="company",
            query="Acme Corp",
            url="https://www.acme.com",
            mode="auto",
            output_dir=str(tmp_path / "company-run"),
        ),
        crawler,
    )

    assert resp.success is True
    assert resp.total_records >= 1


@pytest.mark.asyncio
async def test_dispatcher_falls_back_to_seeds_for_saved_mode(tmp_path) -> None:
    from scout.core.platform.run import run_use_case

    resp = await run_use_case(
        RunRequest(
            use_case="company",
            query="Adobe",
            mode="saved",
            output_dir=str(tmp_path / "company-run"),
        ),
    )

    assert resp.success is True
    assert resp.total_records > 0


@pytest.mark.asyncio
async def test_live_prism_runner_is_bounded_to_v1_bundle(monkeypatch, tmp_path) -> None:
    """PRISM V1 is company/social + careers + investor + news, not every vertical."""

    from scout.core.platform.run import run_use_case
    from scout.core.use_cases.runners import (
        careers,
        company,
        investor,
        locations,
        news,
        research,
        social,
    )

    called: list[str] = []
    forbidden_called: list[str] = []

    def fake_runner(name: str):
        async def _run(_req, _crawler):
            called.append(name)
            return [
                {
                    "objectID": f"{name}_record",
                    "record_type": name,
                    "citations": [
                        {
                            "source_id": f"src_{name}",
                            "source_url": "https://example.com",
                            "field": "url",
                            "claim": name,
                        }
                    ],
                }
            ]

        return _run

    def forbidden_runner(name: str):
        async def _run(_req, _crawler):
            forbidden_called.append(name)
            raise AssertionError("PRISM V1 should not run this vertical")

        return _run

    monkeypatch.setattr(company, "run_company", fake_runner("company"))
    monkeypatch.setattr(careers, "run_careers", fake_runner("careers"))
    monkeypatch.setattr(investor, "run_investor", fake_runner("investor"))
    monkeypatch.setattr(news, "run_news", fake_runner("news"))
    monkeypatch.setattr(social, "run_social", fake_runner("social"))
    monkeypatch.setattr(research, "run_research", forbidden_runner("research"))
    monkeypatch.setattr(locations, "run_locations", forbidden_runner("locations"))

    resp = await run_use_case(
        RunRequest(
            use_case="prism",
            query="Example",
            url="https://example.com",
            mode="auto",
            output_dir=str(tmp_path / "prism-run"),
        ),
        crawler=object(),
    )

    assert resp.success is True
    assert called == ["company", "careers", "investor", "news", "social"]
    assert forbidden_called == []
