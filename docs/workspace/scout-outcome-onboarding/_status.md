# Scout Outcome Onboarding Draft Status

Started: 2026-07-09

## Goal

Draft and implement an outcome-first homepage/beta page layer that helps first-time beta testers understand what Scout does, how to test it, and why the output is useful, without damaging the current premium mint neumorphic Scout visual system.

## Checklist

- [x] Design thinking notes written.
- [x] UI/UX constraints recorded.
- [x] Failing tests added for outcome-first copy and demo video frame.
- [x] Homepage and beta page draft implemented.
- [x] Focused tests run.
- [x] Desktop and mobile screenshots rendered.
- [x] Draft shown to Arijit.

## Verification

- `python3 -m pytest tests/unit/website/test_launch_website.py -q` -> 34 passed, 2 warnings.
- Playwright mobile width check at 375px:
  - `/index.html`: `innerWidth=375`, `scrollWidth=375`, `bodyScrollWidth=375`.
  - `/beta.html`: `innerWidth=375`, `scrollWidth=375`, `bodyScrollWidth=375`.

## Screenshots

- `artifacts/outcome-home-desktop.png`
- `artifacts/outcome-beta-desktop.png`
- `artifacts/outcome-home-mobile-playwright.png`
- `artifacts/outcome-beta-mobile-playwright.png`
