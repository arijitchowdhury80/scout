"""SEC EDGAR exec enrichment — CIK matching, Form 4 XML parsing, name reorder.
Injected fetch, no network."""

from __future__ import annotations

import pytest

from scout.core.enrich.sec import (
    SecExec,
    _match_cik,
    _norm_company,
    _parse_form4_owners,
    _reorder_sec_name,
    sec_executives,
)

_FORM4 = """<?xml version="1.0"?>
<ownershipDocument>
  <reportingOwner>
    <reportingOwnerId><rptOwnerName>OTTENHEIMER DAVI</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship><isDirector>0</isDirector><isOfficer>0</isOfficer></reportingOwnerRelationship>
  </reportingOwner>
  <reportingOwner>
    <reportingOwnerId><rptOwnerName>ITTYCHERIA DEV</rptOwnerName></reportingOwnerId>
    <reportingOwnerRelationship><isDirector>1</isDirector><isOfficer>1</isOfficer><officerTitle>President and CEO</officerTitle></reportingOwnerRelationship>
  </reportingOwner>
</ownershipDocument>"""


def test_norm_company_strips_legal_suffixes() -> None:
    assert _norm_company("MongoDB, Inc.") == "mongodb"
    assert _norm_company("Apple Inc.") == "apple"
    assert _norm_company("Alphabet Corporation") == "alphabet"


def test_reorder_sec_name() -> None:
    assert _reorder_sec_name("COOK TIMOTHY D") == "Timothy D Cook"
    assert _reorder_sec_name("ITTYCHERIA DEV") == "Dev Ittycheria"


def test_parse_form4_keeps_only_officers_and_directors() -> None:
    execs = _parse_form4_owners(_FORM4)
    # Ottenheimer is neither officer nor director here -> excluded (the exact
    # false-positive Wikipedia produced for MongoDB).
    assert [(e.name, e.title) for e in execs] == [("Dev Ittycheria", "President and CEO")]


def test_parse_form4_bad_xml_returns_empty() -> None:
    assert _parse_form4_owners("<not valid") == []


def test_match_cik_exact_normalized() -> None:
    tickers = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 1441816, "ticker": "MDB", "title": "MongoDB, Inc."},
    }
    assert _match_cik("MongoDB", tickers) == 1441816
    assert _match_cik("Apple", tickers) == 320193


def test_match_cik_no_confident_match_returns_none() -> None:
    tickers = {"0": {"cik_str": 1, "ticker": "X", "title": "Something Else Inc."}}
    assert _match_cik("Nonexistent Startup", tickers) is None


class _Resp:
    def __init__(self, payload=None, text=""):
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_sec_executives_end_to_end() -> None:
    tickers = {"1": {"cik_str": 1441816, "ticker": "MDB", "title": "MongoDB, Inc."}}
    submissions = {
        "filings": {
            "recent": {
                "form": ["8-K", "4"],
                "accessionNumber": ["0000-00", "0001234567-25-000001"],
                "primaryDocument": ["x.htm", "form4.xml"],
            }
        }
    }

    async def fake_fetch(url: str) -> _Resp:
        if "company_tickers" in url:
            return _Resp(payload=tickers)
        if "submissions" in url:
            return _Resp(payload=submissions)
        return _Resp(text=_FORM4)  # the archive Form 4 doc

    execs = await sec_executives("MongoDB", fetch=fake_fetch)
    assert [(e.name, e.title) for e in execs] == [("Dev Ittycheria", "President and CEO")]
    assert all(isinstance(e, SecExec) for e in execs)


@pytest.mark.asyncio
async def test_sec_executives_no_cik_returns_empty() -> None:
    async def fake_fetch(url: str) -> _Resp:
        return _Resp(payload={"0": {"cik_str": 1, "ticker": "X", "title": "Other Co"}})

    assert await sec_executives("Unknown Private Startup", fetch=fake_fetch) == []


@pytest.mark.asyncio
async def test_sec_executives_never_raises() -> None:
    async def boom(url: str) -> _Resp:
        raise RuntimeError("edgar down")

    assert await sec_executives("MongoDB", fetch=boom) == []
