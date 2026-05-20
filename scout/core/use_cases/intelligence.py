"""Shared intelligence record contracts for Scout verticals."""

from __future__ import annotations

from pydantic import BaseModel, Field

from scout.core.platform.types import Citation


class InvestorAssetRecord(BaseModel):
    schema_version: str = "investor_asset.v1"
    record_type: str = "investor_asset"
    objectID: str
    company: str
    asset_type: str
    url: str
    title: str = ""
    published_at: str = ""
    source_url: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)


class CareerSiteRecord(BaseModel):
    schema_version: str = "career_site.v1"
    record_type: str = "career_site"
    objectID: str
    company: str
    careers_url: str
    ats_platform: str = ""
    departments: list[str] = Field(default_factory=list)
    hiring_signal_summary: str = ""
    source_url: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)


class NewsSignalRecord(BaseModel):
    schema_version: str = "news_signal.v1"
    record_type: str = "news_signal"
    objectID: str
    company: str = ""
    title: str
    url: str
    topic: str = ""
    published_at: str = ""
    summary: str = ""
    source_url: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)


class ResearchRecord(BaseModel):
    schema_version: str = "research_record.v1"
    record_type: str = "research_record"
    objectID: str
    topic: str
    url: str
    title: str = ""
    summary: str = ""
    source_url: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)
