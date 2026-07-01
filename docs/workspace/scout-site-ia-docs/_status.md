# Scout Site IA And Docs Refresh Status

Date: 2026-07-01
Status: Verified locally

## Checklist

- [x] Confirm real repo path is `/Users/arijitchowdhury/Dropbox/AI-Development/Scout`.
- [x] Read existing launch website implementation and tests.
- [x] Load frontend-builder, frontend-design, and UI/UX constraints.
- [x] Record IA/design notes for this change.
- [x] Move playground out of docs and under demo flow.
- [x] Update homepage flow to hero, features/use cases, demo, playground, purchase.
- [x] Update primary navigation mapping.
- [x] Make `/docs` a structured software documentation page.
- [x] Update tests and run verification.
- [x] Remove redundant homepage feature/use-case split.
- [x] Keep Demo active for both demo and playground while scrolling.
- [x] Add structured docs sidebar/table-of-contents layout.

## Verification

- `python3 -m pytest tests/unit/website/test_launch_website.py -q`
  - Result: 23 passed.
- `python3 -m pytest tests/e2e/test_playground_full_e2e.py -q`
  - Result: 2 passed.
- `python3 -m pytest tests/unit/website/test_launch_website.py tests/e2e/test_playground_full_e2e.py -q`
  - Result: 25 passed.
- `python3 -m pytest tests/unit/ -q`
  - Result: 654 passed.
- `ruff check scout/ tests/ && ruff format --check scout/ tests/`
  - Result: all checks passed; 226 files already formatted.
- `python3 -m pytest tests/unit/api/test_auth.py tests/unit/api/test_playground.py -q`
  - Result: 18 passed.
- `python3 -m pyright scout/`
  - Result: 0 errors.
- `ruff check scout/ tests/`
  - Result: all checks passed.
- `ruff format --check scout/ tests/`
  - Result: 226 files already formatted.
- Hosted browser smoke against `https://scout.chowmes.com/`
  - Result: homepage flow is `hero -> use-cases -> demo -> playground -> purchase`.
  - Result: `Features` activates `#use-cases`; `Demo` remains active for `#demo` and `#playground`; `Pricing` activates `#purchase`.
  - Result: `/docs` opens `Technical documentation for Scout.` with `.docs-sidebar` visible.
  - Result: console errors `[]`.
- Hosted playground smoke against `https://scout.chowmes.com/#playground`
  - Result: `scrape + example.com` completed with 1 record and 0 blocked pages.
- `python3 -m pytest tests/unit/api/test_auth.py tests/unit/website/test_launch_website.py tests/e2e/test_playground_full_e2e.py -q`
  - Result: 36 passed.
- `python3 -m pyright scout/`
  - Result: 0 errors, 0 warnings, 0 informations.
- `ruff check scout/ tests/unit/website/test_launch_website.py tests/e2e/test_playground_full_e2e.py tests/unit/api/test_auth.py && ruff format --check scout/ tests/unit/website/test_launch_website.py tests/e2e/test_playground_full_e2e.py tests/unit/api/test_auth.py`
  - Result: all checks passed; 110 files already formatted.
- Browser smoke against `python3 -m http.server 8766 --directory website`
  - Result: desktop and mobile homepage/docs checks passed; static server stopped.
- Direct `file://` smoke for `website/index.html`
  - Result: logo loaded at `300x112`; demo GIF loaded at `1280x720`; console errors: none.
- `python3 -m pytest tests/unit/website/test_launch_website.py tests/e2e/test_playground_full_e2e.py -q`
  - Result: 25 passed.
