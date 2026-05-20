# AGENTS.md — Scout Project

## What This Is

Scout is a self-hosted web intelligence platform built on Crawl4AI. It replaces Apify in PRISM's intel modules and serves as a general-purpose crawler for Codex and other tools.

## Resume Context

- **SESSION.md** — current task, exact resume action, all decisions, remaining work
- **Memory** — `~/.Codex/projects/-Users-arijitchowdhury-AI-Development-PIP/memory/`
- **Workspace** — `docs/workspace/scout-core/` — PRD (with acceptance criteria), pre-mortem, strategy

## Hard Constraints

1. **workflow-build-module skill FIRST** — never build before Phase 1 thinking docs exist
2. **TDD always** — tests before implementation, RED before GREEN
3. **Three test layers required** — unit + integration + contract before component is "done"
4. **No raw dicts crossing boundaries** — Pydantic on every response
5. **pyright must be clean** — run `python3 -m pyright scout/` before committing
6. **structlog** — approved structured logger; stdout only (no file logging Phase 1)
7. **FastAPI DI** — ScoutCrawler is lifespan singleton injected via `Depends(get_crawler)` in `deps.py`
8. **Smoke test before PRISM integration** — HTTP stack must pass AC-1 through AC-8 first

## Verification

```bash
python3 -m pytest tests/unit/ -v          # 70 tests, fast
python3 -m pytest tests/ -v               # +6 integration (needs network)
python3 -m pyright scout/                 # 0 errors required
ruff check scout/ && ruff format --check scout/
```

## Phase Status

- Phase 1 core library: **COMPLETE**
- Phase 1 API layer: **COMPLETE**
- Phase 1 Docker: **COMPLETE**
- Phase 2 Codex skill file: **COMPLETE** (not yet registered)
- Platform execution modes: **FOUNDATION COMPLETE**
- Multi-use-case run surface: **FOUNDATION COMPLETE** for CLI + HTTP + skill docs
- **Smoke test: PENDING** ← do this next
- **PRISM Phase 4 integration: PENDING** ← main goal, after smoke test

## Current Platform Direction

Scout is not only a product scraper or job hunter. Treat it as a reusable web
intelligence platform with vertical processors for company, PRISM, investor,
careers, jobs, products, news, and generic research. All high-level runs must
preserve the standard artifact contract:

```text
manifest.json
records.json
records.jsonl
source_pages.json
blocked_pages.json
validation.json
extraction_report.md
```

Supported execution modes are `auto`, `crawl4ai`, `webfetch`, `websearch`,
`browser`, `saved`, and `api`. Browser fallback is secondary and should only be
used when regular acquisition is blocked, sparse, JS-heavy, or explicitly being
verified.

Private job profiles, resume-derived preferences, API tokens, and personal
research profiles stay in vault-backed or ignored local files. Public examples
must use sanitized fixtures.

## Reference Artifacts

| Path | Purpose |
|---|---|
| `docs/workspace/scout-core/04-prd.md` | Acceptance criteria AC-1 through AC-12 |
| `docs/workspace/scout-core/05-pre-mortem.md` | Risks — T3 Docker, T5 FastAPI DI |
| `scout/core/types.py` | All Pydantic contracts — change here first |
| `scout/api/deps.py` | `get_crawler()` dependency — import this for test overrides |
| `scout/skill/scout.md` | Codex skill definition |


<claude-mem-context>
# Memory Context

# [Scout] recent context, 2026-05-20 4:10am EDT

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (16,524t read) | 171,466t work | 90% savings

### May 13, 2026
S381 Get up to speed on Scout skill, evaluate its codebase, fix installation instructions and directory structure issues, enhance it to scrape products for Algolia indexing, and refactor it to be a pure scraper without unnecessary bloat. Work includes brainstorming, planning, documentation, and GitHub updates. (May 13 at 5:05 PM)
S380 Verify if a new scout repository needs to be created on GitHub, and plan migration strategy for Scout standalone package (May 13 at 5:05 PM)
### May 14, 2026
S382 Get up to speed on Scout skill, evaluate its codebase, fix installation instructions and directory structure issues, enhance it to scrape products for Algolia indexing, and refactor it to be a pure scraper without unnecessary bloat. (May 14 at 2:13 AM)
S386 Validate Scout's architectural fit for multiple intelligence-gathering use cases: company research, investor analysis, job applications, prospect research, and social platforms. Confirm appropriate scope and positioning. (May 14 at 7:56 PM)
### May 20, 2026
1638 2:17a 🟣 Provider-Agnostic Platform Abstraction Layer Implemented
1639 " ✅ Use Case Handlers Abstraction Created
1640 " ✅ CLI and HTTP API Structure Aligned with Platform Architecture
1642 " 🟣 HTTP API Application with FastAPI, AuthMiddleware, and Router Registration
1643 " 🟣 API Router Test Suite with Mocked Crawler and Dependency Injection
1644 " 🟣 Use Case Registry with 10 Domain-Specific Intelligence Operations
1645 " 🟣 PRISM Company Intelligence Record Schemas
1646 " 🟣 CLI Extended with High-Level Use Case Subcommands
1647 2:18a 🟣 Execution Mode Contract and Provider Ladder Tests Written
1648 " 🟣 Execution Mode Enum and Provider Ladder Implementation
1649 " ✅ RunRequest Updated to Accept Execution Mode Parameter
1651 " 🟣 Intelligence Use Case Record Schemas TDD Tests Written
1652 2:19a 🟣 Intelligence Record Schemas Implemented for Investor, Careers, News, Research
1655 " 🟣 Use Case Runner Tests Written — TDD for Multi-Domain V1 Extraction
1656 2:20a ✅ Platform Dispatcher Integrated with Execution Mode Provider Ladder
1658 " 🔵 Use Case Runner Tests Reveal Missing Registry Entries for Company and Careers
1659 2:21a 🟣 V1 Intelligence Use Case Runners Implemented — Deterministic Seed Records
1660 " ✅ Platform Dispatcher Integrated with Intelligence Use Case Runners
1662 " 🟣 CLI Run Subcommands Extended with Mode Option and Use Case Discovery
1663 " 🟣 HTTP API /run/{use_case} Endpoint Tests Added
1665 2:22a 🔵 CLI and API Run Endpoint Tests Fail — Implementation Gaps Identified
1666 " 🟣 CLI Run Commands Extended with --mode Option
1667 " 🟣 HTTP API /run/{use_case} Endpoint Implemented
1668 " ✅ HTTP API Main App Integrated with /run/{use_case} Router
1671 2:23a ✅ RunRequest.use_case Made Optional for API Endpoint
1674 " ✅ API Test Fixed — Status/Version Assertions Moved to Health Test
1684 2:26a 🔵 Products Use Case Test Reveals Implementation Gap
1685 " ✅ Products Use Case Added to Intelligence Runner
1686 " ✅ Platform Dispatcher Updated to Route Products Through Intelligence Runner
1696 4:00a 🔵 Scout Provenance Architecture: SourceEvidence and FetchResult Core Types
1697 4:01a 🔵 Intelligence Use Case "Research" Architecture: Seed Records with Deferred Evidence Collection
1698 4:03a 🔵 Citation/Provenance Tracking Pattern Across Runner Implementations
1699 " 🔵 Record Schemas: Source Attribution Fields Vary Across Domains
1700 " 🟣 Citation Type and Source ID Determinism: TDD Test Cases Added
1701 " 🟣 Artifact and Validation Tests: Citation Registry with Content Hashing
1702 4:04a 🟣 Use Case Integration Tests: Citations Required Across All Record Types
1703 " 🟣 Job Runner Citation Tests: Multi-Field Citations with Source Tracking
1704 " 🔵 Test Execution: All Citation Tests Fail with Expected ImportError
1705 " 🟣 Citation Type and Deterministic source_id Implementation
1706 4:05a 🟣 Source Page Registry Entry Generation with Content Hashing
1707 " 🟣 Citation Field Added to PRISM Record Types
1708 " 🟣 Citation Fields Added to Intelligence Record Types
1709 " 🟣 Citation Fields Added to Jobs Record Types
1710 " 🟣 Citation Field Added to ProductRecord
1711 4:06a 🟣 Intelligence Runner Citations Implementation with Seed Sources
1712 4:07a 🟣 Jobs Runner Citations Implementation with Profile-Level Sources
1713 " 🔵 All Citation Tests Passing: TDD GREEN Phase Complete
1714 " 🔵 Citation Implementation Plan: 3 of 5 Steps Completed
1716 " ✅ README Updated with source_pages.json Citation Registry Explanation
1717 " ✅ Architecture Documentation: Citation Model Section Added

Access 171k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>
