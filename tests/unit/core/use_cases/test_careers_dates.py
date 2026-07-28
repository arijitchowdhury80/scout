"""FX-11 Build 3 — careers 24h jobs filter.

Tests the role-date extraction + posted_within_hours filter in
scout.core.use_cases.runners.careers, and the end-to-end wiring through
run_careers(). No fabrication: roles with no discoverable date must pass
through untouched with a flag, never a guessed date.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from scout.core.platform.types import RunRequest
from scout.core.types import ScoutMetadata, ScrapeResponse
from scout.core.use_cases.intelligence import CareerRoleRecord
from scout.core.use_cases.runners.careers import (
    _extract_roles,
    _filter_roles_within_hours,
    _parse_posted_at,
)


def _now() -> datetime:
    return datetime(2026, 7, 27, 12, 0, 0, tzinfo=timezone.utc)


def test_parse_posted_at_relative_days_ago():
    posted_at, found, reason = _parse_posted_at("Senior Engineer — Posted 3 days ago", _now())

    assert found is True
    assert reason == ""
    assert posted_at is not None
    assert datetime.fromisoformat(posted_at) == _now() - timedelta(days=3)


def test_parse_posted_at_posted_today():
    posted_at, found, reason = _parse_posted_at("Support Lead — Posted today", _now())

    assert found is True
    assert datetime.fromisoformat(posted_at) == _now()


def test_parse_posted_at_iso_date():
    posted_at, found, reason = _parse_posted_at("Data Analyst (2026-07-20)", _now())

    assert found is True
    assert datetime.fromisoformat(posted_at).date().isoformat() == "2026-07-20"


def test_parse_posted_at_no_date_found_sets_flag_and_reason():
    posted_at, found, reason = _parse_posted_at("Product Designer - Mobile", _now())

    assert posted_at is None
    assert found is False
    assert reason == "no_date_on_page"


def test_extract_roles_from_markdown_returns_deduped_titles():
    markdown = (
        "# Join Acme\n\n"
        "Senior Software Engineer - Backend\n"
        "Product Designer - Mobile\n"
        "Senior Software Engineer - Backend\n"  # duplicate line
    )

    roles = _extract_roles(markdown, _now())

    titles = [role.title for role in roles]
    assert titles == [
        "Senior Software Engineer - Backend",
        "Product Designer - Mobile",
    ]
    assert all(isinstance(role, CareerRoleRecord) for role in roles)
    assert all(role.posted_at_found is False for role in roles)


def test_filter_roles_within_hours_keeps_recent_and_dateless_drops_stale():
    fresh = CareerRoleRecord(
        title="Fresh Role",
        posted_at=(_now() - timedelta(hours=2)).isoformat(),
        posted_at_found=True,
    )
    stale = CareerRoleRecord(
        title="Stale Role",
        posted_at=(_now() - timedelta(days=10)).isoformat(),
        posted_at_found=True,
    )
    dateless = CareerRoleRecord(
        title="Dateless Role",
        posted_at=None,
        posted_at_found=False,
        posted_at_reason="no_date_on_page",
    )

    kept = _filter_roles_within_hours([fresh, stale, dateless], posted_within_hours=24, now=_now())

    kept_titles = {role.title for role in kept}
    assert "Fresh Role" in kept_titles
    assert "Stale Role" not in kept_titles
    assert "Dateless Role" in kept_titles  # no fabrication — passes through, flagged


def test_filter_roles_within_hours_none_returns_all_roles_unfiltered():
    roles = [
        CareerRoleRecord(title="A", posted_at=None, posted_at_found=False),
        CareerRoleRecord(
            title="B",
            posted_at=(_now() - timedelta(days=100)).isoformat(),
            posted_at_found=True,
        ),
    ]

    kept = _filter_roles_within_hours(roles, posted_within_hours=None, now=_now())

    assert kept == roles


def _meta(url: str = "https://example.com") -> ScoutMetadata:
    return ScoutMetadata(url=url, crawled_at="2026-07-27T00:00:00Z")


def _scrape_ok(url: str, markdown: str, links: list[str] | None = None) -> ScrapeResponse:
    return ScrapeResponse(
        success=True,
        url=url,
        markdown=markdown,
        links=links or [],
        metadata=_meta(url),
        duration_ms=100,
    )


def _mock_crawler(responses: dict[str, ScrapeResponse]) -> MagicMock:
    crawler = MagicMock()

    async def _scrape(req):
        for pattern, resp in responses.items():
            if pattern in req.url:
                return resp
        return ScrapeResponse(
            success=False,
            url=req.url,
            markdown="",
            metadata=_meta(req.url),
            error="404",
            duration_ms=10,
        )

    crawler.scrape = AsyncMock(side_effect=_scrape)
    return crawler


@pytest.mark.asyncio
async def test_run_careers_applies_posted_within_hours_filter_to_roles():
    from scout.core.use_cases.runners.careers import run_careers

    crawler = _mock_crawler(
        {
            "/careers": _scrape_ok(
                "https://www.acme.com/careers",
                "# Join Acme\n\n"
                "We use Greenhouse to manage applications.\n"
                "Senior Software Engineer - Backend — Posted 1 hour ago\n"
                "Product Designer - Mobile — Posted 90 days ago\n"
                "Support Specialist\n",  # no date on page → passes through, flagged
            ),
        }
    )

    req = RunRequest(
        use_case="careers",
        query="Acme Corp",
        url="https://www.acme.com",
        mode="auto",
        posted_within_hours=24,
    )
    records = await run_careers(req, crawler)

    assert len(records) == 1
    roles = records[0]["roles"]
    titles = {role["title"] for role in roles}
    assert "Senior Software Engineer - Backend — Posted 1 hour ago" in titles
    assert "Support Specialist" in titles
    assert "Product Designer - Mobile — Posted 90 days ago" not in titles
    dateless = next(r for r in roles if r["title"] == "Support Specialist")
    assert dateless["posted_at_found"] is False
    assert dateless["posted_at_reason"] == "no_date_on_page"


@pytest.mark.asyncio
async def test_run_careers_without_filter_returns_all_roles():
    from scout.core.use_cases.runners.careers import run_careers

    crawler = _mock_crawler(
        {
            "/careers": _scrape_ok(
                "https://www.acme.com/careers",
                "# Join Acme\n\nProduct Designer - Mobile — Posted 90 days ago\n",
            ),
        }
    )

    req = RunRequest(use_case="careers", query="Acme Corp", url="https://www.acme.com", mode="auto")
    records = await run_careers(req, crawler)

    roles = records[0]["roles"]
    assert len(roles) == 1
