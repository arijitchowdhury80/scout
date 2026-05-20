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

# [Scout] recent context, 2026-05-20 4:45am EDT

Legend: 🎯session 🔴bugfix 🟣feature 🔄refactor ✅change 🔵discovery ⚖️decision 🚨security_alert 🔐security_note
Format: ID TIME TYPE TITLE
Fetch details: get_observations([IDs]) | Search: mem-search skill

Stats: 50 obs (14,169t read) | 98,591t work | 86% savings

### May 13, 2026
S381 Get up to speed on Scout skill, evaluate its codebase, fix installation instructions and directory structure issues, enhance it to scrape products for Algolia indexing, and refactor it to be a pure scraper without unnecessary bloat. Work includes brainstorming, planning, documentation, and GitHub updates. (May 13 at 5:05 PM)
S380 Verify if a new scout repository needs to be created on GitHub, and plan migration strategy for Scout standalone package (May 13 at 5:05 PM)
### May 14, 2026
S382 Get up to speed on Scout skill, evaluate its codebase, fix installation instructions and directory structure issues, enhance it to scrape products for Algolia indexing, and refactor it to be a pure scraper without unnecessary bloat. (May 14 at 2:13 AM)
S386 Validate Scout's architectural fit for multiple intelligence-gathering use cases: company research, investor analysis, job applications, prospect research, and social platforms. Confirm appropriate scope and positioning. (May 14 at 7:56 PM)
### May 20, 2026
1721 4:11a 🔵 Test Failure Details: Report Missing Coverage Section
1722 " 🟣 Citation Coverage Summary Implementation in Artifacts
1723 " ✅ Coverage Summary Implementation Applied to Artifacts Module
1724 " 🔵 Citation Coverage Report Test Passing: GREEN Phase Complete
1725 " ✅ Distribution Documentation: Citation-Grade Provenance Artifacts
1726 " ✅ Execution Modes Documentation: Provider-Agnostic Citation Normalization
1727 " ✅ Execution Modes Documentation Updated with Citation Normalization Section
1728 " ✅ Skill Guidance Updated: Citations Section and User Communication Standards
1729 " ✅ Use Cases Documentation: Citation Requirements Standard Across All Verticals
1730 " ✅ Use Cases Documentation Patch Applied: Citation Requirements Codified
1731 4:12a ✅ Project Wiki Updated: Citation ADR and Development Log Entries
1733 " 🔵 Citation Implementation Plan: 4 of 5 Steps Complete, Final Verification Underway
1735 " 🔵 Citation Test Suite Verification: All 19 Tests Pass with Clean Code Quality
1736 " 🔵 Type Safety Verification Complete: Pyright Passes with Zero Errors
1738 " 🔵 Full Unit Test Suite Verification: 169 Tests Pass with Zero Regressions
1739 4:13a 🔵 Code Formatting Complete: All 97 Files Properly Formatted
1740 " 🔵 Citation Implementation Complete: All Verification Checks Pass
1741 " 🔵 Final Quality Check: Ruff Linting Confirms All Checks Pass
1742 " 🔵 Final Type Safety Verification: Pyright Confirms Zero Issues
1743 " 🔵 Full Test Suite Complete: 175 Passed, 2 Skipped, Zero Regressions
1744 4:14a 🔵 Live CLI Test: Citation Implementation Working End-to-End
1745 " 🔵 Live Jobs Runner Test: Citation Implementation Working for Job Hunter
1747 " 🔵 Citation Validation: Bidirectional Linkage Verified, 100% Coverage Achieved
1748 " 🔵 HTTP Server Started: Scout API Ready for Citation Testing
1749 " 🔵 HTTP Server Ready: Scout API Online and Accepting Requests
1750 " 🔵 HTTP API Health Check: Service Online and Responsive
1751 " 🔵 HTTP API Citation Endpoint: /run/company Working End-to-End
1752 " 🔵 HTTP API Citation Validation: 100% Coverage, Bidirectional Linkage Verified
1753 " 🔵 HTTP Server Shutdown: All Tests Complete, No Errors
1754 4:15a ✅ Project Vault Updated: Citation Verification Complete Log Entry
1755 " 🔵 Citation Implementation Plan: 100% Complete - All 5 Steps Delivered
1756 4:25a 🔵 Scout mode system and crawl4ai integration architecture
1757 " 🔵 Scout mode-based provider fallback system and execution flow
1758 4:30a 🟣 Target Matrix Expanded to Include Estée Lauder and British Airways
1759 4:31a 🔵 Test for Target Matrix Fails — Module Not Implemented
1762 " 🟣 Scout Target Matrix Module Implemented
1763 " 🔵 Target Matrix Tests: 3 Pass, 1 Fails on Use-Case Filtering
1764 " 🔵 Test Failure: targets_for_use_case() Includes Secondary Targets by Default
1766 " 🔵 Test Failure: Products Use Case Missing Nike — Secondary Target Expected
1768 4:32a 🟣 Scout Target Matrix Tests All Pass — TDD Cycle Complete
1769 " ✅ Target Matrix Documentation Created
1770 " ✅ Use-Cases Documentation Updated to Reference Target Matrix
1771 " ✅ Architecture Documentation Enhanced with Validation Targets Section
1774 4:33a ✅ Scout Skill Documentation Updated with Target Matrix Reference
1777 " ✅ Documentation Examples Standardized to Primary Targets; Decision Recorded in Project Wiki
1779 " 🔵 Code Format Check Fails on targets.py
1781 4:34a 🔵 Test Suite and Type Checking Pass; Formatting-Only Issue Remains
1783 " 🔵 Code Formatting Applied Successfully; All Tests Still Pass
1784 " 🟣 Scout Target Matrix Feature Complete — All Quality Checks Pass
1787 " 🟣 Full Unit Test Suite Passes — 173 Tests Green, No Regressions

Access 99k tokens of past work via get_observations([IDs]) or mem-search skill.
</claude-mem-context>
