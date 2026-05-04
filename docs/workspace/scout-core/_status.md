# Scout Core — Workspace Status

**Updated**: 2026-05-03

## Phase 1: Thinking — COMPLETE

- [x] 01-strategy.md
- [x] 02-value-prop.md
- [x] 03-assumptions.md
- [x] 04-prd.md
- [x] 05-pre-mortem.md

## Phase 2: Implementation — IN PROGRESS

### What was built BEFORE Phase 1 docs (out of order):
- `scout/core/types.py` — all Pydantic contracts ✅
- `scout/core/version.py` — version pin ✅
- `scout/core/modes/scrape.py` + tests ✅
- `scout/core/modes/crawl.py` + tests ✅
- `scout/core/modes/extract.py` + tests ✅
- `scout/core/modes/map.py` + tests ✅
- `scout/core/modes/screenshot.py` + tests ✅
- `scout/core/crawler.py` (ScoutCrawler) + tests ✅ (41 unit tests total)

### SOP Violations Found (must fix before continuing):
1. **No function-level docstrings** on any mode function or ScoutCrawler methods (CodingSOPs §6, §8)
2. **Exception handling**: all modes catch bare `except Exception` — specific exceptions should come first (CodingSOPs §1)
3. **Test naming**: doesn't follow `test_{what}_{condition}_{expected}` pattern (TestingSOPs)
4. **Missing test layers**: integration tests = zero, contract tests = zero (TestingSOPs — module NOT done)
5. **Mock strategy**: API test delegation uses `unittest.mock.patch` (monkey-patching) not adapter injection (TestingSOPs mock strategy)
6. **pyright --strict**: never been run. Unknown type errors.
7. **Pydantic `version` field**: CodingSOPs §7 says every model needs a version field. Scout models don't have it. (OPEN QUESTION — see PRD §8 Q5)
8. **`structlog` vs `logging`**: SOPs say `import logging; logger = logging.getLogger(__name__)`. Implementation uses `structlog`. structlog IS a structured logger but this deviates from the SOP literal.

### Critical Unknowns (from pre-mortem T1):
- `fit_markdown` attribute path on CrawlResult — must verify
- `arun_many()` async iteration pattern — must verify
- Both must be smoke-tested against real Crawl4AI before API layer is built

## Next Actions (in order)

1. SOP validation pass — fix all violations listed above (Task #20)
2. Crawl4AI smoke test — verify fit_markdown path + arun_many pattern (pre-mortem T1)
3. Build integration tests for all 5 modes (TestingSOPs Layer 2)
4. Build contract tests (TestingSOPs Layer 3)
5. Then: Task #12 — FastAPI API layer
6. Then: Task #13 — Docker
7. Then: Task #14 — Claude skill

## What Has NOT Been Done
- Phase 1 thinking was done AFTER implementation (out of order — corrected now)
- Integration tests: zero
- Contract tests: zero
- pyright --strict: never run
- Crawl4AI smoke test against real URL: never run
- Docker: not built
- FastAPI API layer: not built
- Claude skill: not built
