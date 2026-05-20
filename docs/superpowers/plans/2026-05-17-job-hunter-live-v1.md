# Job Hunter Live V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Scout Job Hunter Live V1 so Scout can ingest seed job URLs, detect ATS/source platform, extract normalized job records, score them against a strict Director+ career profile, and write standard Scout artifacts.

**Architecture:** Keep personal matching data out of the public repo. The repo implements generic job URL ingestion, ATS detection, extraction, scoring, and artifact writing. Private profiles live in the vault or user-provided YAML and flow through `JobSearchProfile`.

**Tech Stack:** Python 3.11+, Pydantic v2, Typer, pytest, pyright, ruff, Crawl4AI-backed acquisition, provider-agnostic Scout platform contracts.

---

## Scope

This slice implements URL-seeded job extraction and matching. It does not yet implement daily scheduling or broad AI-company discovery. Those follow after URL ingestion, extraction, scoring, and artifacts are stable.

## Seed Platforms

| Platform | Seed Purpose |
|---|---|
| Greenhouse | Ooma, Eve, Gradial examples; high-value first parser. |
| Ashby | Kong example; JavaScript shell and adapter/fallback test. |
| Workday | Salesforce example; canonicalization and fallback test. |
| Native careers | Intuit example; generic parser fallback test. |

## File Structure

Create:

- `scout/core/use_cases/jobs_sources.py`: job URL input models, ATS/source detection, URL normalization.
- `scout/core/use_cases/jobs_extractors.py`: HTML/markdown extraction helpers for Greenhouse, Ashby, Workday/native fallback.
- `scout/core/use_cases/jobs_scoring.py`: deterministic profile/job scoring and reject reasons.
- `tests/fixtures/jobs/greenhouse_eve_director_cs.html`: sanitized static fixture for a Greenhouse Director CS page.
- `tests/fixtures/jobs/greenhouse_ooma_strategic_partnerships.html`: sanitized static fixture for a Greenhouse Strategic Partnerships page.
- `tests/fixtures/jobs/ashby_kong_js_shell.html`: sanitized static fixture representing an Ashby JS shell / incomplete fetch.
- `tests/fixtures/jobs/native_intuit_sample.html`: sanitized static fixture for native careers fallback behavior.
- `tests/unit/core/use_cases/test_jobs_sources.py`
- `tests/unit/core/use_cases/test_jobs_extractors.py`
- `tests/unit/core/use_cases/test_jobs_scoring.py`

Modify:

- `scout/core/use_cases/jobs.py`: add `job_urls`, stronger profile fields, match result fields, and source evidence fields.
- `scout/core/use_cases/jobs_runner.py`: accept URL-seeded runs, extract job postings, score them, write records and validation findings.
- `scout/cli.py`: add `--job-url` repeatable option or `--job-urls-file` to `scout run jobs`.
- `README.md`: document URL-seeded Job Hunter usage.
- `docs/distribution.md`: document private-profile handling.

## Task 1: Job Source Detection

**Files:**
- Create: `scout/core/use_cases/jobs_sources.py`
- Modify: `scout/core/use_cases/jobs.py`
- Test: `tests/unit/core/use_cases/test_jobs_sources.py`

- [ ] **Step 1: Write failing tests**

Create `tests/unit/core/use_cases/test_jobs_sources.py`:

```python
from scout.core.use_cases.jobs_sources import JobSourcePlatform, detect_job_source_platform


def test_detects_greenhouse_job_board_url() -> None:
    assert (
        detect_job_source_platform("https://job-boards.greenhouse.io/eve/jobs/4245857009")
        == JobSourcePlatform.GREENHOUSE
    )


def test_detects_ashby_job_url() -> None:
    assert (
        detect_job_source_platform("https://jobs.ashbyhq.com/kong/21690b70-385c-49bf-9942-a949b65642fe/application")
        == JobSourcePlatform.ASHBY
    )


def test_detects_workday_job_url() -> None:
    assert (
        detect_job_source_platform("https://salesforce.wd12.myworkdayjobs.com/External_Career_Site/job/California---San-Francisco/Customer-Success-Manager--Director_JR341622")
        == JobSourcePlatform.WORKDAY
    )


def test_unknown_native_careers_url_is_native() -> None:
    assert (
        detect_job_source_platform("https://jobs.intuit.com/job/-/-/27595/94741635984")
        == JobSourcePlatform.NATIVE
    )
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_sources.py -v
```

Expected: fails because `jobs_sources.py` does not exist.

- [ ] **Step 3: Implement source detection**

Create `scout/core/use_cases/jobs_sources.py`:

```python
"""Job source detection and URL normalization."""

from __future__ import annotations

from enum import Enum
from urllib.parse import urlparse


class JobSourcePlatform(str, Enum):
    GREENHOUSE = "greenhouse"
    ASHBY = "ashby"
    WORKDAY = "workday"
    NATIVE = "native"
    UNKNOWN = "unknown"


def detect_job_source_platform(url: str) -> JobSourcePlatform:
    host = urlparse(url).netloc.lower()
    if "greenhouse.io" in host:
        return JobSourcePlatform.GREENHOUSE
    if "ashbyhq.com" in host:
        return JobSourcePlatform.ASHBY
    if "myworkdayjobs.com" in host:
        return JobSourcePlatform.WORKDAY
    if host:
        return JobSourcePlatform.NATIVE
    return JobSourcePlatform.UNKNOWN
```

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_sources.py -v
```

Expected: 4 passed.

## Task 2: Extend Job Profile And Record Contracts

**Files:**
- Modify: `scout/core/use_cases/jobs.py`
- Test: `tests/unit/core/use_cases/test_jobs_contracts.py`

- [ ] **Step 1: Write failing contract tests**

Add to `tests/unit/core/use_cases/test_jobs_contracts.py`:

```python
from scout.core.use_cases.jobs import JobPostingRecord, JobSearchProfile


def test_job_search_profile_accepts_seed_job_urls_and_strict_filters() -> None:
    profile = JobSearchProfile(
        desired_titles=["Director, Enterprise Customer Success"],
        salary_min_usd=250000,
        seniority=["Director", "Senior Director", "VP"],
        target_companies=["Adobe"],
        job_urls=["https://job-boards.greenhouse.io/eve/jobs/4245857009"],
        must_have_terms=["AI", "enterprise", "customer success"],
        reject_terms=["intern", "support representative"],
    )

    assert profile.salary_min_usd == 250000
    assert profile.job_urls == ["https://job-boards.greenhouse.io/eve/jobs/4245857009"]
    assert "AI" in profile.must_have_terms


def test_job_posting_record_carries_match_and_reject_reasons() -> None:
    record = JobPostingRecord(
        objectID="job_eve_4245857009",
        company="Eve",
        title="Director of Enterprise Customer Success",
        url="https://job-boards.greenhouse.io/eve/jobs/4245857009",
        salary_min=225000,
        salary_max=280000,
        ats_platform="greenhouse",
        match_score=92,
        match_reasons=["Director-level enterprise CS role", "AI-native company"],
        reject_reasons=[],
        source_confidence=0.95,
    )

    assert record.match_score == 92
    assert "AI-native company" in record.match_reasons
    assert record.source_confidence == 0.95
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_contracts.py::test_job_search_profile_accepts_seed_job_urls_and_strict_filters tests/unit/core/use_cases/test_jobs_contracts.py::test_job_posting_record_carries_match_and_reject_reasons -v
```

Expected: fails because fields do not exist.

- [ ] **Step 3: Implement contract fields**

Modify `JobSearchProfile`:

```python
job_urls: list[str] = Field(default_factory=list)
must_have_terms: list[str] = Field(default_factory=list)
reject_terms: list[str] = Field(default_factory=list)
```

Modify `JobPostingRecord`:

```python
match_score: int = Field(default=0, ge=0, le=100)
match_reasons: list[str] = Field(default_factory=list)
reject_reasons: list[str] = Field(default_factory=list)
source_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
source_platform: str = ""
raw_source_url: str = ""
```

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_contracts.py -v
```

Expected: all job contract tests pass.

## Task 3: Greenhouse Fixture Extraction

**Files:**
- Create: `scout/core/use_cases/jobs_extractors.py`
- Create: `tests/fixtures/jobs/greenhouse_eve_director_cs.html`
- Test: `tests/unit/core/use_cases/test_jobs_extractors.py`

- [ ] **Step 1: Write failing extraction test**

Create `tests/unit/core/use_cases/test_jobs_extractors.py`:

```python
from pathlib import Path

from scout.core.use_cases.jobs_extractors import extract_job_posting_from_html
from scout.core.use_cases.jobs_sources import JobSourcePlatform


def test_extracts_greenhouse_director_cs_fixture() -> None:
    html = Path("tests/fixtures/jobs/greenhouse_eve_director_cs.html").read_text()

    record = extract_job_posting_from_html(
        html=html,
        url="https://job-boards.greenhouse.io/eve/jobs/4245857009",
        platform=JobSourcePlatform.GREENHOUSE,
    )

    assert record.company == "Eve"
    assert record.title == "Director of Enterprise Customer Success"
    assert record.salary_min == 225000
    assert record.salary_max == 280000
    assert record.ats_platform == "greenhouse"
    assert "enterprise customer success" in record.description.lower()
```

- [ ] **Step 2: Add sanitized fixture**

Create `tests/fixtures/jobs/greenhouse_eve_director_cs.html`:

```html
<html>
  <body>
    <h1>Director of Enterprise Customer Success</h1>
    <div class="company-name">Eve</div>
    <div class="location">Remote, United States</div>
    <div class="content">
      <p>Eve is an AI platform for legal teams.</p>
      <p>This enterprise customer success leader will own executive relationships, adoption, renewals, and expansion.</p>
      <p>The salary range for this role is $225,000 - $280,000.</p>
    </div>
    <a href="https://job-boards.greenhouse.io/eve/jobs/4245857009#app">Apply</a>
  </body>
</html>
```

- [ ] **Step 3: Run test to verify RED**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_extractors.py::test_extracts_greenhouse_director_cs_fixture -v
```

Expected: fails because extractor does not exist.

- [ ] **Step 4: Implement minimal extractor**

Create `scout/core/use_cases/jobs_extractors.py` with BeautifulSoup-based title, company, location, description, apply URL, and salary range extraction. Use deterministic regex for salary ranges such as `$225,000 - $280,000`.

- [ ] **Step 5: Run test to verify GREEN**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_extractors.py -v
```

Expected: test passes.

## Task 4: Strict Match Scoring

**Files:**
- Create: `scout/core/use_cases/jobs_scoring.py`
- Test: `tests/unit/core/use_cases/test_jobs_scoring.py`

- [ ] **Step 1: Write failing scoring tests**

Create `tests/unit/core/use_cases/test_jobs_scoring.py`:

```python
from scout.core.use_cases.jobs import JobPostingRecord, JobSearchProfile
from scout.core.use_cases.jobs_scoring import score_job_posting


def test_scores_ai_enterprise_director_cs_role_high() -> None:
    profile = JobSearchProfile(
        desired_titles=["Director Enterprise Customer Success"],
        salary_min_usd=250000,
        seniority=["Director", "Senior Director", "VP"],
        role_keywords=["AI", "enterprise", "customer success", "renewals", "expansion"],
        reject_terms=["intern", "support representative"],
    )
    record = JobPostingRecord(
        objectID="job_eve_4245857009",
        company="Eve",
        title="Director of Enterprise Customer Success",
        url="https://job-boards.greenhouse.io/eve/jobs/4245857009",
        salary_min=225000,
        salary_max=280000,
        description="AI platform. Enterprise customer success, executive relationships, renewals, adoption, expansion.",
    )

    scored = score_job_posting(record, profile)

    assert scored.match_score >= 85
    assert "Director-level role" in scored.match_reasons
    assert scored.reject_reasons == []


def test_rejects_below_compensation_threshold() -> None:
    profile = JobSearchProfile(salary_min_usd=250000, seniority=["Director"])
    record = JobPostingRecord(
        objectID="job_low_comp",
        company="Example",
        title="Director Customer Success",
        url="https://example.com/job",
        salary_min=150000,
        salary_max=180000,
        description="Enterprise customer success role.",
    )

    scored = score_job_posting(record, profile)

    assert scored.match_score < 70
    assert "Compensation below threshold" in scored.reject_reasons
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_scoring.py -v
```

Expected: fails because scorer does not exist.

- [ ] **Step 3: Implement deterministic scorer**

Implement `score_job_posting(record, profile)` to:

- Add points for seniority/title matches.
- Add points for role keyword matches across title + description.
- Add points when `salary_max >= profile.salary_min_usd`.
- Add reject reason when compensation upper bound is below threshold.
- Add reject reason when reject terms appear.
- Clamp score between 0 and 100.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_scoring.py -v
```

Expected: all scoring tests pass.

## Task 5: URL-Seeded Runner

**Files:**
- Modify: `scout/core/use_cases/jobs_runner.py`
- Test: `tests/unit/core/use_cases/test_jobs_runner.py`

- [ ] **Step 1: Write failing runner test with saved fixture provider**

Add to `tests/unit/core/use_cases/test_jobs_runner.py`:

```python
import json
from pathlib import Path

from scout.core.platform.types import RunRequest
from scout.core.use_cases.jobs_runner import run_jobs_use_case


def test_run_jobs_use_case_extracts_and_scores_seed_job_url(tmp_path) -> None:
    profile_path = tmp_path / "job-profile.yaml"
    fixture_path = Path("tests/fixtures/jobs/greenhouse_eve_director_cs.html")
    output_dir = tmp_path / "jobs-run"
    profile_path.write_text(
        f"""
desired_titles:
  - Director Enterprise Customer Success
salary_min_usd: 250000
seniority:
  - Director
role_keywords:
  - AI
  - enterprise
  - customer success
  - renewals
  - expansion
job_urls:
  - fixture://{fixture_path}
""".strip()
    )

    response = run_jobs_use_case(
        RunRequest(use_case="jobs", profile_path=str(profile_path), output_dir=str(output_dir))
    )

    assert response.success is True
    assert response.total_records == 1

    records = json.loads((output_dir / "records.json").read_text())
    assert records[0]["record_type"] == "job_posting"
    assert records[0]["company"] == "Eve"
    assert records[0]["match_score"] >= 85
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_runner.py::test_run_jobs_use_case_extracts_and_scores_seed_job_url -v
```

Expected: fails because runner only emits target company records.

- [ ] **Step 3: Implement fixture URL ingestion**

In `jobs_runner.py`, when `profile.job_urls` exists:

- Read `fixture://` paths for tests.
- Detect source platform from URL or fixture label.
- Extract `JobPostingRecord`.
- Score it.
- Write job records instead of target company records.
- Add source evidence entry for each URL/fixture.

- [ ] **Step 4: Run test to verify GREEN**

Run:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_runner.py -v
```

Expected: all runner tests pass.

## Task 6: CLI URL Seeds

**Files:**
- Modify: `scout/cli.py`
- Test: `tests/unit/cli/test_run_commands.py`

- [ ] **Step 1: Write failing CLI test**

Add to `tests/unit/cli/test_run_commands.py`:

```python
from pathlib import Path


def test_run_jobs_accepts_job_url_option() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("job-profile.yaml").write_text(
            """
desired_titles:
  - Director Enterprise Customer Success
salary_min_usd: 250000
seniority:
  - Director
role_keywords:
  - AI
  - enterprise
  - customer success
""".strip()
        )

        result = runner.invoke(
            app,
            [
                "run",
                "jobs",
                "--profile",
                "job-profile.yaml",
                "--job-url",
                "https://job-boards.greenhouse.io/eve/jobs/4245857009",
                "--output-dir",
                "jobs-run",
            ],
        )

        assert result.exit_code == 0
        assert '"success": true' in result.output
```

- [ ] **Step 2: Run test to verify RED**

Run:

```bash
python3 -m pytest tests/unit/cli/test_run_commands.py::test_run_jobs_accepts_job_url_option -v
```

Expected: fails because `--job-url` does not exist.

- [ ] **Step 3: Add CLI option**

Modify `run_jobs` to accept a repeatable `--job-url` option and pass it through `RunRequest.extra` or a typed field added to `RunRequest`.

- [ ] **Step 4: Run CLI tests**

Run:

```bash
python3 -m pytest tests/unit/cli/test_run_commands.py -v
```

Expected: CLI tests pass.

## Task 7: Documentation And Vault Sync

**Files:**
- Modify: `README.md`
- Modify: `docs/distribution.md`
- Vault: `Projects/Scout/wiki/use-cases/job-hunter/arijit-ai-transition-test-scenario.md`

- [ ] **Step 1: Document public usage**

Add a public README example:

```bash
scout run jobs \
  --profile ./job-profile.yaml \
  --job-url https://job-boards.greenhouse.io/eve/jobs/4245857009 \
  --output-dir ./scout-runs/job-hunter
```

- [ ] **Step 2: Document privacy boundary**

State that private candidate profiles should live outside the public repo, preferably in the user vault or local ignored config.

- [ ] **Step 3: Append vault dev-log**

Record implementation completion and verification evidence in the Scout vault after tests pass.

## Verification Gate

Run all commands before claiming completion:

```bash
python3 -m pytest tests/unit/core/use_cases/test_jobs_sources.py -v
python3 -m pytest tests/unit/core/use_cases/test_jobs_extractors.py -v
python3 -m pytest tests/unit/core/use_cases/test_jobs_scoring.py -v
python3 -m pytest tests/unit/core/use_cases/test_jobs_runner.py -v
python3 -m pytest tests/unit/cli/test_run_commands.py -v
python3 -m pytest tests/unit/ -v
python3 -m pytest tests/ -v
python3 -m pyright scout/
ruff check scout/ tests/
ruff format --check scout/ tests/
```

Expected:

- All new unit tests pass.
- Existing unit suite remains green.
- Full test suite remains green, with live retail tests skipped only when their env flags are not enabled.
- Pyright reports 0 errors.
- Ruff check and format check pass.

## Follow-On Slices

After this slice:

1. Add live HTTP acquisition for job URLs with a five-minute timeout cap.
2. Add Greenhouse board/API adapter where public board metadata is available.
3. Add Ashby adapter or browser fallback path for JS-shell pages.
4. Add Workday canonical search fallback.
5. Add company discovery for AI companies and daily scheduled monitoring.

## Implementation Status

**Updated:** 2026-05-19

Completed in this slice:

- ATS/source detection for Greenhouse, Ashby, Workday, native careers, and unknown URLs.
- `JobSearchProfile` support for seed `job_urls`, `must_have_terms`, and `reject_terms`.
- `JobPostingRecord` support for `match_score`, `match_reasons`, `reject_reasons`, `source_confidence`, `source_platform`, and `raw_source_url`.
- Greenhouse-style saved HTML extraction for title, company, location, description, salary range, apply URL, source platform, and stable `objectID`.
- Deterministic strict scoring for Director+ seniority, title overlap, keyword/must-have matches, compensation threshold, and reject terms.
- `scout run jobs --job-url` CLI option.
- URL-seeded runner path for saved `fixture://` evidence, source evidence artifacts, and blocked-page reporting for unsupported live URLs.
- Public sanitized Director CS scoring demo profile and fixture.

Verified:

- `python3 -m pytest tests/unit/ -v`: 152 passed.
- `python3 -m pytest tests/ -v`: 158 passed, 2 skipped, using escalated access for Crawl4AI cache writes.
- `python3 -m pyright scout/`: 0 errors.
- `ruff check scout/ tests/`: passed.
- `ruff format --check scout/ tests/`: 90 files already formatted.

Still pending:

- Live HTTP acquisition for public job URLs.
- Greenhouse board/API adapter.
- Ashby adapter/browser fallback for JavaScript shell pages.
- Workday and native careers canonicalization/search fallback.
- Company discovery and scheduled monitoring.
