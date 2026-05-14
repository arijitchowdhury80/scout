# CLAUDE.md — Scout Project

## What This Is

Scout is a self-hosted web intelligence platform built on Crawl4AI. It replaces Apify in PRISM's intel modules and serves as a general-purpose crawler for Claude and other tools.

## Resume Context

- **SESSION.md** — current task, exact resume action, all decisions, remaining work
- **Memory** — `~/.claude/projects/-Users-arijitchowdhury-AI-Development-PIP/memory/`
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
- Phase 2 Claude skill file: **COMPLETE** (not yet registered)
- **Smoke test: PENDING** ← do this next
- **PRISM Phase 4 integration: PENDING** ← main goal, after smoke test

## Reference Artifacts

| Path | Purpose |
|---|---|
| `docs/workspace/scout-core/04-prd.md` | Acceptance criteria AC-1 through AC-12 |
| `docs/workspace/scout-core/05-pre-mortem.md` | Risks — T3 Docker, T5 FastAPI DI |
| `scout/core/types.py` | All Pydantic contracts — change here first |
| `scout/api/deps.py` | `get_crawler()` dependency — import this for test overrides |
| `scout/skill/scout.md` | Claude Code skill definition |
