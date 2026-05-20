"""Job hunter and career monitoring contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
import yaml

from scout.core.platform.types import Citation


class TargetCompanyInput(BaseModel):
    name: str
    website: str = ""
    careers_url: str = ""
    linkedin_url: str = ""
    industry: str = ""


class JobSearchProfile(BaseModel):
    desired_titles: list[str] = Field(default_factory=list)
    role_keywords: list[str] = Field(default_factory=list)
    salary_min_usd: int | None = None
    salary_max_usd: int | None = None
    locations: list[str] = Field(default_factory=list)
    seniority: list[str] = Field(default_factory=list)
    target_industries: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)
    target_companies: list[TargetCompanyInput] = Field(default_factory=list)
    job_urls: list[str] = Field(default_factory=list)
    must_have_terms: list[str] = Field(default_factory=list)
    reject_terms: list[str] = Field(default_factory=list)


class TargetCompanyRecord(BaseModel):
    schema_version: str = "target_company.v1"
    record_type: str = "target_company"
    objectID: str
    company: str
    website: str = ""
    careers_url: str = ""
    linkedin_url: str = ""
    industry: str = ""
    reason_matched: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)


class JobPostingRecord(BaseModel):
    schema_version: str = "job_posting.v1"
    record_type: str = "job_posting"
    objectID: str
    company: str
    title: str
    url: str
    location: str = ""
    remote_type: str = ""
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str = "USD"
    department: str = ""
    description: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    apply_url: str = ""
    ats_platform: str = ""
    source_platform: str = ""
    raw_source_url: str = ""
    source_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    posted_at: str = ""
    first_seen_at: str = ""
    last_seen_at: str = ""
    matched_terms: list[str] = Field(default_factory=list)
    match_score: int = Field(default=0, ge=0, le=100)
    match_reasons: list[str] = Field(default_factory=list)
    reject_reasons: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)


def load_job_search_profile(path: Path) -> JobSearchProfile:
    loaded: Any = yaml.safe_load(path.read_text())
    if not isinstance(loaded, dict):
        raise ValueError("Job search profile must contain a YAML mapping.")
    return JobSearchProfile.model_validate(loaded)
