# Scout Website Polish Status

Date: 2026-06-29

## Goal

Polish the launch homepage without changing the approved direction:

- add a real Scout logo/mark;
- reduce perceived clutter by about 10%;
- keep the warm industrial design language;
- fix homepage section anchoring and scroll-aware nav state.

## Status

- Design notes: complete
- Implementation: complete
- Tests: complete
- Verification: complete
- Vault update: complete

## Verification

- `python3 -m pytest tests/unit/website/test_launch_website.py -q` passed 13 tests.
- `python3 -m pytest tests/unit/website/test_launch_website.py tests/unit/test_launch_readiness_check.py -q` passed 20 tests.
- `python3 -m ruff check scout/api/launch_site.py scout/api/middleware/auth.py tests/unit/website/test_launch_website.py` passed.
- Browser validation with Playwright passed on desktop and mobile:
  - logo visible;
  - section nav active state updates;
  - anchor clicks land sections below sticky header;
  - mobile nav remains visible.
- Route smoke on `http://127.0.0.1:8431` returned 200 for `/`,
  `/assets/scout-mark.svg`, `/assets/scout-wordmark.svg`, `/pricing`,
  `/status`, `/beta`, and `/quickstart`.
