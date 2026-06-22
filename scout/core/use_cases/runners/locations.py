"""Locations runner — scrapes store locator pages for addresses and contact info."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from pydantic import BaseModel, Field

from scout.core.crawler import ScoutCrawler
from scout.core.platform.types import Citation, RunRequest
from scout.core.use_cases.runners.base import (
    evidence_from_scrape,
    make_citation,
    safe_scrape,
)

_LOCATOR_PATHS = [
    "/locations",
    "/stores",
    "/store-locator",
    "/find-a-store",
    "/contact/locations",
    "/offices",
]

_PHONE_PATTERN = re.compile(r"(?:\+1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")

_ADDRESS_PATTERN = re.compile(
    r"\d{1,5}\s+[\w\s.]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Road|Rd|Drive|Dr|"
    r"Lane|Ln|Way|Court|Ct|Place|Pl|Circle|Cir|Highway|Hwy|Suite|Ste)\.?"
    r"[,\s]+(?:[\w\s]+,\s*)?[A-Z]{2}\s+\d{5}(?:-\d{4})?",
    re.I,
)

_COORDS_PATTERN = re.compile(r"(-?\d{1,3}\.\d{3,8})[,\s]+(-?\d{1,3}\.\d{3,8})")


class LocationRecord(BaseModel):
    schema_version: str = "location.v1"
    record_type: str = "location"
    objectID: str
    company: str
    name: str = ""
    address: str = ""
    phone: str = ""
    latitude: float | None = None
    longitude: float | None = None
    source_url: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)


def _base_url(req: RunRequest) -> str:
    if req.url:
        return req.url.rstrip("/")
    if req.targets:
        return req.targets[0].rstrip("/")
    name = req.query.strip().lower().replace(" ", "")
    return f"https://www.{name}.com"


def _company_name(req: RunRequest) -> str:
    return req.query.strip() or "unknown"


def _extract_locations(markdown: str, company: str, source_url: str) -> list[dict]:
    addresses = _ADDRESS_PATTERN.findall(markdown)
    phones = _PHONE_PATTERN.findall(markdown)
    coords = _COORDS_PATTERN.findall(markdown)

    locations: list[dict] = []
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")

    for i, address in enumerate(addresses[:20]):
        phone = phones[i] if i < len(phones) else ""
        lat = float(coords[i][0]) if i < len(coords) else None
        lng = float(coords[i][1]) if i < len(coords) else None

        if lat is not None and (lat < -90 or lat > 90):
            lat = None
        if lng is not None and (lng < -180 or lng > 180):
            lng = None

        locations.append(
            {
                "objectID": f"location_{slug}_{i}",
                "address": address.strip(),
                "phone": phone.strip(),
                "latitude": lat,
                "longitude": lng,
            }
        )

    return locations


async def run_locations(req: RunRequest, crawler: ScoutCrawler) -> list[dict]:
    base = _base_url(req)
    company = _company_name(req)
    slug = re.sub(r"[^a-z0-9]+", "_", company.lower()).strip("_")

    source = None
    all_markdown = ""
    locator_url = ""

    for path in _LOCATOR_PATHS:
        url = urljoin(base + "/", path.lstrip("/"))
        resp = await safe_scrape(crawler, url)
        if resp:
            source = evidence_from_scrape(url, resp)
            locator_url = url
            all_markdown = resp.markdown
            break

    if not source:
        return []

    raw_locations = _extract_locations(all_markdown, company, locator_url)
    if not raw_locations:
        return [
            LocationRecord(
                objectID=f"location_{slug}_page",
                company=company,
                name=f"{company} locations page",
                source_url=locator_url,
                confidence=0.4,
                citations=[
                    make_citation(
                        source,
                        "url",
                        locator_url,
                        "Locations page found but no addresses extracted",
                    )
                ],
            ).model_dump(mode="json")
        ]

    records: list[dict] = []
    for loc in raw_locations:
        records.append(
            LocationRecord(
                objectID=loc["objectID"],
                company=company,
                address=loc["address"],
                phone=loc["phone"],
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                source_url=locator_url,
                confidence=0.7 if loc["address"] else 0.4,
                citations=[make_citation(source, "address", loc["address"], loc["address"][:200])],
            ).model_dump(mode="json")
        )

    return records
