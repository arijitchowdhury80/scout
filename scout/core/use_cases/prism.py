"""PRISM company intelligence contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from scout.core.platform.types import Citation


class CompanyRecord(BaseModel):
    schema_version: str = "company.v1"
    record_type: str = "company"
    objectID: str
    name: str
    website: str = ""
    linkedin_url: str = ""
    description: str = ""
    industry: str = ""
    source_urls: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)


class CompanySocialRecord(BaseModel):
    schema_version: str = "company_social.v1"
    record_type: str = "company_social"
    objectID: str
    company: str
    platform: str
    url: str
    handle: str = ""
    provider: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)


class ExecutiveRecord(BaseModel):
    schema_version: str = "executive.v1"
    record_type: str = "executive"
    objectID: str
    company: str
    name: str
    title: str = ""
    bio: str = ""
    linkedin_url: str = ""
    profile_url: str = ""
    source_url: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)
