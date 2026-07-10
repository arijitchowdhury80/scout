# Mobile UX Sprint Status

Date: 2026-07-09
Status: Verified locally

## Goal

Stop the public Scout website from behaving like a desktop page collapsed into a
long mobile roll. Phones need a purpose-built journey: understand Scout, see
proof, know what to test, and get an API key.

## Baseline Evidence

Playwright audit against `website/index.html`:

- iPhone SE: 5,866px page height, 8.8 screens.
- iPhone 14: 5,762px page height, 6.8 screens.
- Pixel 7: 5,678px page height, 6.2 screens.
- Galaxy S20: 5,923px page height, 7.4 screens.
- iPad mini: 3,959px page height, 3.9 screens.
- Phone header height: 189px.
- Live console status on phones says it is static and should run on desktop,
  but the full console still occupies the page.
- Multiple tabs/nav/footer links were under 44px tall.

Screenshots: `artifacts/mobile-ux-audit/*-before.png`

## Working Hypothesis

Root cause is not horizontal overflow. It is information architecture: desktop
sections are stacked onto phones even when those components are not appropriate
for mobile.

## Required Fix

- Compact mobile header.
- Hide full desktop console on phone widths.
- Hide full desktop outcome/video walkthrough on phone widths.
- Hide long desktop capability grid on phone widths.
- Add a mobile-specific proof journey that keeps the premium Scout visual system
  while prioritizing comprehension and API-key signup.
- Keep tablet and desktop functional.
- Ensure touch targets are at least 44px.

## Verification Plan

- Static unit tests for mobile-specific markup/CSS.
- Playwright screenshots and metrics for iPhone, Android, iPad, and Android
  tablet viewports.
- Click checks for primary mobile CTAs, tabs on tablet, pricing modal, beta form
  fields, and video playback visibility.

## Implemented Fix

- Replaced the phone homepage stack with a phone-specific proof journey.
- Hid the desktop console, long outcome/video walkthrough, and desktop
  capability grid on phone widths.
- Kept the full console available on tablet and desktop.
- Reduced the mobile header from the baseline 189px to 64px.
- Added touch-target hardening across public navigation, buttons, tabs, footer
  links, legal pages, pricing modal, and beta signup fields.
- Preserved the premium Scout visual language: same tokens, same surface
  treatment, no new marketing theme.

## Final Verification Evidence

- `python3 -m pytest tests/unit/website/test_launch_website.py -q`
  - Result: 36 passed, 2 warnings.
- `git diff --check`
  - Result: clean.
- Playwright public-page sweep against FastAPI/static website routes:
  - Routes: `/`, `/pricing`, `/beta`, `/legal`, `/terms`, `/privacy`.
  - Viewports: 360px phone, 375px iPhone, 768px iPad, 800px Android tablet.
  - Result: no horizontal overflow and zero visible interactive targets below
    44px on every checked route/viewport.
- Phone homepage height reduction:
  - iPhone SE: 5,866px / 8.8 screens to 2,719px / 4.1 screens.
  - Pixel 7: 5,678px / 6.2 screens to 2,575px / 2.8 screens.
- FastAPI click path:
  - Home `Get API key` opens `/beta`.
  - Mobile proof `See pricing` opens `/pricing`.
  - Pricing modal opens and focuses company name.
  - Beta form fields accept input without horizontal overflow.
- Tablet click path:
  - Console remains visible.
  - Console tabs activate on iPad mini and Android tablet.

## Remaining Notes

- Mobile video controls are visible and the media metadata loads. Headless
  mobile/touch playback did not advance time, so autoplay should not be treated
  as verified; users can still play from the native controls.
- The expected UI/UX SOP path was not present locally:
  `~/Library/CloudStorage/GoogleDrive-arijit.chowdhury@algolia.com/My Drive/AI-Docs/Obsidian/ArijitOS-Brain/Standards/UIUXDesignSOP/index.md`.
  This sprint used the local frontend-builder and ui-validator constraints as
  the fallback standard.
