# Scout Launch Website Status

Date: 2026-06-28
Status: In progress

## Checklist

- [x] Design thinking written.
- [x] UI/UX constraints written.
- [x] Supadesign IndustrialGray direction selected.
- [x] Static homepage implemented.
- [x] Browser/static verification completed.
- [x] Final notes and next steps documented.

## Scope

Build the first private-beta Scout website surface, separate from the broken
Scout app UI. The website should position Scout, explain local vs hosted usage,
show the artifact/evidence model, and guide users to install locally or join the
hosted beta.

## Verification

Command run through Playwright against `python3 -m http.server 8766 --directory
website`:

- desktop viewport: `1440x1000`
- mobile viewport: `390x844`
- required content assertions passed
- link inventory found 14 links
- console errors/warnings: 0

Screenshots:

- `validation-output/website-scout-launch/desktop.png`
- `validation-output/website-scout-launch/mobile.png`

