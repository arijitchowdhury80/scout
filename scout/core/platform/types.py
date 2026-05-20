"""Provider-agnostic platform contracts for Scout."""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class FetchProviderKind(str, Enum):
    WEBSEARCH = "websearch"
    HOST_WEBFETCH = "host_webfetch"
    CRAWL4AI = "crawl4ai"
    HOST_BROWSER = "host_browser"
    CDP = "cdp"
    SAVED = "saved"
    PDF = "pdf"
    ATS = "ats"
    SOCIAL = "social"
    API = "api"


def stable_source_id(
    provider: FetchProviderKind | str, source_url: str, final_url: str = ""
) -> str:
    identity = "|".join(
        [str(provider), source_url.strip(), final_url.strip() or source_url.strip()]
    )
    return f"src_{hashlib.sha1(identity.encode('utf-8')).hexdigest()[:16]}"


class Citation(BaseModel):
    source_id: str
    source_url: str
    field: str
    claim: str
    snippet: str = ""
    selector: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class SourceEvidence(BaseModel):
    source_id: str = ""
    provider: FetchProviderKind
    source_url: str
    final_url: str = ""
    fetched_at: str
    status_code: int | None = None
    blocked: bool = False
    error: str = ""
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def set_source_id(self) -> SourceEvidence:
        if not self.source_id:
            self.source_id = stable_source_id(self.provider, self.source_url, self.final_url)
        if not self.final_url:
            self.final_url = self.source_url
        return self


class FetchResult(BaseModel):
    evidence: SourceEvidence
    markdown: str = ""
    html: str = ""
    dom_snapshot: str = ""
    text: str = ""
    links: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class ValidationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ValidationFinding(BaseModel):
    severity: ValidationSeverity
    code: str
    message: str
    record_id: str = ""
    source_url: str = ""


class ArtifactFiles(BaseModel):
    manifest: str = ""
    records_json: str = ""
    records_jsonl: str = ""
    source_pages_json: str = ""
    blocked_pages_json: str = ""
    validation_json: str = ""
    report_md: str = ""


class RunManifest(BaseModel):
    run_id: str
    use_case: str
    query: str = ""
    started_at: str
    finished_at: str = ""
    providers_attempted: list[FetchProviderKind] = Field(default_factory=list)
    output_dir: str
    total_records: int = 0
    total_sources: int = 0
    total_blocked: int = 0
    artifacts: ArtifactFiles = Field(default_factory=ArtifactFiles)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class RunRequest(BaseModel):
    use_case: str = ""
    query: str = ""
    mode: str = "auto"
    url: str = ""
    targets: list[str] = Field(default_factory=list)
    profile_path: str = ""
    job_urls: list[str] = Field(default_factory=list)
    output_dir: str
    providers: list[FetchProviderKind] = Field(default_factory=list)
    max_targets: int = Field(default=25, gt=0)
    max_records: int = Field(default=250, gt=0)


class RunResponse(BaseModel):
    success: bool
    use_case: str
    output_dir: str = ""
    manifest: RunManifest | None = None
    total_records: int = 0
    error: str = ""
