"""Balanced validation target matrix for Scout verticals."""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field


class TargetSegment(str, Enum):
    PRIVATE_B2B_SAAS = "private_b2b_saas"
    PRIVATE_RETAIL_COMMERCE = "private_retail_commerce"
    PUBLIC_COMPANY = "public_company"
    PUBLIC_HARD_SITE_RETAIL = "public_hard_site_retail"
    PUBLIC_TRAVEL_AIRLINE = "public_travel_airline"
    SECONDARY = "secondary"


class TargetMetadata(BaseModel):
    name: str
    segment: TargetSegment
    primary_use: str
    website_url: str = ""
    use_cases: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)


_PRIMARY_TARGETS: tuple[TargetMetadata, ...] = (
    TargetMetadata(
        name="Algolia",
        segment=TargetSegment.PRIVATE_B2B_SAAS,
        primary_use="PRISM, company, careers, blogs, docs",
        website_url="https://www.algolia.com/",
        use_cases=["company", "prism", "careers", "news", "blogs", "docs", "research"],
    ),
    TargetMetadata(
        name="Constructor",
        segment=TargetSegment.PRIVATE_B2B_SAAS,
        primary_use="PRISM, competitor intel, company, careers, blogs/docs",
        website_url="https://constructor.com/",
        use_cases=["company", "prism", "careers", "news", "blogs", "docs", "research"],
    ),
    TargetMetadata(
        name="L.L.Bean",
        segment=TargetSegment.PRIVATE_RETAIL_COMMERCE,
        primary_use="ecommerce, product catalog, careers, company",
        website_url="https://www.llbean.com/",
        use_cases=["company", "prism", "careers", "products", "news", "blogs"],
        aliases=["LL Bean", "llbean"],
    ),
    TargetMetadata(
        name="Patagonia",
        segment=TargetSegment.PRIVATE_RETAIL_COMMERCE,
        primary_use="ecommerce, product catalog, company, sustainability/blog content",
        website_url="https://www.patagonia.com/",
        use_cases=["company", "prism", "careers", "products", "news", "blogs"],
    ),
    TargetMetadata(
        name="Adobe",
        segment=TargetSegment.PUBLIC_COMPANY,
        primary_use="company, investor, careers, blogs/news",
        website_url="https://www.adobe.com/",
        use_cases=["company", "prism", "investor", "careers", "news", "blogs"],
    ),
    TargetMetadata(
        name="Home Depot",
        segment=TargetSegment.PUBLIC_COMPANY,
        primary_use="public retail, investor, careers, product catalog, news",
        website_url="https://www.homedepot.com/",
        use_cases=["company", "prism", "investor", "careers", "products", "news", "blogs"],
        aliases=["The Home Depot"],
    ),
    TargetMetadata(
        name="Estée Lauder",
        segment=TargetSegment.PUBLIC_HARD_SITE_RETAIL,
        primary_use="hard-site product/category fallback and blocked-page handling",
        website_url="https://www.esteelauder.com/",
        use_cases=["company", "prism", "investor", "careers", "products", "news", "blogs"],
        aliases=["Estee Lauder", "Estée Lauder Companies", "Estee Lauder Companies"],
    ),
    TargetMetadata(
        name="British Airways",
        segment=TargetSegment.PUBLIC_TRAVEL_AIRLINE,
        primary_use="travel company intel, careers, research",
        website_url="https://www.britishairways.com/",
        use_cases=[
            "company",
            "prism",
            "investor",
            "careers",
            "news",
            "blogs",
            "research",
        ],
        aliases=["BA", "british-airways"],
    ),
)

_SECONDARY_TARGETS: tuple[TargetMetadata, ...] = (
    TargetMetadata(
        name="Nike",
        segment=TargetSegment.SECONDARY,
        primary_use="public retail product/catalog and brand validation",
        website_url="https://www.nike.com/",
        use_cases=["company", "products", "news", "blogs"],
    ),
    TargetMetadata(
        name="Amplience",
        segment=TargetSegment.SECONDARY,
        primary_use="alternate private B2B SaaS target",
        website_url="https://amplience.com/",
        use_cases=["company", "prism", "careers", "news", "blogs", "docs", "research"],
    ),
    TargetMetadata(
        name="Salesforce",
        segment=TargetSegment.SECONDARY,
        primary_use="optional public SaaS investor/careers/company validation",
        website_url="https://www.salesforce.com/",
        use_cases=["company", "prism", "investor", "careers", "news", "blogs"],
    ),
    TargetMetadata(
        name="Intuit",
        segment=TargetSegment.SECONDARY,
        primary_use="optional public careers validation",
        website_url="https://www.intuit.com/",
        use_cases=["company", "careers", "investor", "news", "blogs"],
    ),
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def primary_targets() -> list[TargetMetadata]:
    return list(_PRIMARY_TARGETS)


def secondary_targets() -> list[TargetMetadata]:
    return list(_SECONDARY_TARGETS)


def all_targets() -> list[TargetMetadata]:
    return [*primary_targets(), *secondary_targets()]


def get_target(name: str) -> TargetMetadata | None:
    needle = _slug(name)
    for target in all_targets():
        names = [target.name, *target.aliases]
        if any(_slug(candidate) == needle for candidate in names):
            return target
    return None


def target_url_for_name(name: str) -> str:
    target = get_target(name)
    return target.website_url if target else ""


def targets_for_use_case(use_case: str, include_secondary: bool = False) -> list[TargetMetadata]:
    candidates = all_targets() if include_secondary else primary_targets()
    return [target for target in candidates if use_case in target.use_cases]
