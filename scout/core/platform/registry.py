"""Use-case registry for high-level Scout run commands."""

from __future__ import annotations

from pydantic import BaseModel


class UseCaseMetadata(BaseModel):
    name: str
    description: str


_USE_CASES: dict[str, UseCaseMetadata] = {
    "company": UseCaseMetadata(
        name="company",
        description="Company website, about page, leadership, socials, and key URLs.",
    ),
    "products": UseCaseMetadata(
        name="products",
        description="Product catalog extraction and Algolia-ready records.",
    ),
    "jobs": UseCaseMetadata(
        name="jobs",
        description="Job hunter, company discovery, and career monitoring.",
    ),
    "careers": UseCaseMetadata(
        name="careers",
        description="Careers page, ATS detection, departments, and hiring signals.",
    ),
    "prism": UseCaseMetadata(
        name="prism",
        description="PRISM company and prospect intelligence evidence collection.",
    ),
    "investor": UseCaseMetadata(
        name="investor",
        description="Investor relations, filings, metrics, and financial documents.",
    ),
    "research": UseCaseMetadata(
        name="research",
        description="Generic web research and opportunity discovery.",
    ),
    "website-quality": UseCaseMetadata(
        name="website-quality",
        description="Website quality and competitive gap analysis.",
    ),
    "docs": UseCaseMetadata(
        name="docs",
        description="Documentation and knowledge-base extraction.",
    ),
    "news": UseCaseMetadata(
        name="news",
        description="Newsroom and company signal monitoring.",
    ),
    "social": UseCaseMetadata(
        name="social",
        description="Social signal normalization from explicit providers.",
    ),
    "locations": UseCaseMetadata(
        name="locations",
        description="Store locator and location data extraction.",
    ),
}


def list_use_cases() -> list[str]:
    return list(_USE_CASES)


def get_use_case(name: str) -> UseCaseMetadata | None:
    return _USE_CASES.get(name)
