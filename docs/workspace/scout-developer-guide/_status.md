# Scout Developer Guide Status

Feature: Static beta developer guide page

Status: Verified

## Checklist

- [x] Design thinking documented.
- [x] UI/UX constraints documented.
- [x] RED tests added and verified.
- [x] Static guide page implemented.
- [x] Public guide route implemented.
- [x] Website navigation and README updated.
- [x] Verification passed.

## Verification

- `python3 -m pytest tests/unit/website/test_launch_website.py::test_launch_website_has_beta_onboarding_pages tests/unit/website/test_launch_website.py::test_api_serves_launch_website_beta_onboarding_pages_without_auth -q` -> `2 passed, 2 warnings`.
- `python3 -m pytest tests/unit/website/test_launch_website.py -q` -> `12 passed, 2 warnings`.
- `python3 -m pytest tests/unit/test_launch_governance_docs.py -q` -> `29 passed`.
- Playwright Chromium against `scout serve --host 127.0.0.1 --port 8769` -> desktop and mobile loaded `/guide`, showed the local CLI, hosted beta API, and Swagger boundary sections, and had no console errors.
