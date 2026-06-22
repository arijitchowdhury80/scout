# CLAUDE.md — Scout Project

## What This Is

Scout is a self-hosted web intelligence platform built on Crawl4AI. It replaces Apify in PRISM's intel modules and serves as a general-purpose crawler for Claude and other tools.

## Resume Context

- **SESSION.md** — current task, exact resume action, all decisions, remaining work
- **Memory** — `~/.claude/projects/-Users-arijitchowdhury-AI-Development-Scout/memory/`
- **Plan** — `~/.claude/plans/hidden-jumping-crayon.md` — 9-phase code-complete plan (approved 2026-06-22)
- **Workspace** — `docs/workspace/scout-core/` — PRD (with acceptance criteria), pre-mortem, strategy

## Hard Constraints

1. **workflow-build-module skill FIRST** — never build before Phase 1 thinking docs exist
2. **TDD always** — tests before implementation, RED before GREEN
3. **Three test layers required** — unit + integration + contract before component is "done"
4. **No raw dicts crossing boundaries** — Pydantic on every response
5. **pyright must be clean** — run `python3 -m pyright scout/` before committing
6. **structlog** — approved structured logger; stdout only (no file logging Phase 1)
7. **FastAPI DI** — ScoutCrawler + RunDB are lifespan singletons injected via `Depends()` in `deps.py`
8. **Smoke test before PRISM integration** — HTTP stack must pass AC-1 through AC-8 first

## Verification

```bash
python3 -m pytest tests/unit/ -v          # 305 tests, fast
python3 -m pytest tests/ -v               # +14 integration (needs network)
python3 -m pyright scout/                 # 0 errors required
ruff check scout/ && ruff format --check scout/
```

## Phase Status

- Phase 1 core library / API / Docker: **COMPLETE**
- Products mode: **REAL end-to-end** (incl. browser fallback + User Browser CDP capture)
- Acquisition engine (structure + harvest + CDP-attach + raw://): **COMPLETE** — integration tested
- PRISM endpoints (`POST /structure`, `POST /harvest`): **SHIPPED** — branch pushed
- **Plan Phase 1 — SQLite Run Persistence: DONE** — RunDB + write-through cache
- **Plan Phase 2 — SSE Streaming: DONE** — EventBus + SSE endpoint
- **Plan Phase 3 — Algolia Push: DONE** — save_objects integration
- **Plan Phase 4 — Verticals Wave 1: DONE** — company, careers, investor, news runners
- **Plan Phase 5 — Verticals Wave 2: DONE** — research, docs, social, locations, website-quality, products wiring, PRISM aggregate
- **Plan Phase 6 — Quality Bugs: DONE** — junk filter, variant dedup, brand fallback, API key endpoint
- **Plan Phase 7 — Docker: DONE** — Dockerfile, compose, nginx, systemd
- **Plan Phase 8 — CI/CD: DONE** — GitHub Actions workflow
- **Plan Phase 9 — Browse-Harvest UI: DONE** — run_id persistence, Browser tab
- **ALL 9 PLAN PHASES COMPLETE** — 367 tests, pyright 0 errors, ruff clean

## Reference Artifacts

| Path | Purpose |
|---|---|
| `~/.claude/plans/hidden-jumping-crayon.md` | 9-phase code-complete plan |
| `docs/workspace/scout-core/04-prd.md` | Acceptance criteria AC-1 through AC-12 |
| `docs/workspace/scout-core/05-pre-mortem.md` | Risks — T3 Docker, T5 FastAPI DI |
| `scout/core/types.py` | All Pydantic contracts — change here first |
| `scout/api/db.py` | RunDB — async SQLite persistence |
| `scout/api/deps.py` | `get_crawler()` + `get_run_db()` DI helpers |
| `scout/skill/scout.md` | Claude Code skill definition |
