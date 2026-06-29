# Scout Demo GIF Status

Feature: Beta-safe launch website demo GIF

Status: Verified

## Checklist

- [x] Red tests added for homepage copy, public asset serving, and real GIF file.
- [x] Red tests verified.
- [x] Design thinking documented.
- [x] UI/UX constraints documented.
- [x] Demo GIF generated.
- [x] Homepage demo section implemented.
- [x] Public asset route implemented.
- [x] Verification passed.

## Verification

- `python3 -m pytest tests/unit/website/test_launch_website.py::test_launch_website_exposes_hosted_beta_checkout_form_without_secrets tests/unit/website/test_launch_website.py::test_api_serves_launch_website_static_assets_without_auth tests/unit/website/test_launch_website.py::test_launch_website_demo_gif_is_real_beta_safe_media -q` -> `3 passed, 2 warnings`.
- `python3 -m pytest tests/unit/website/test_launch_website.py -q` -> `12 passed, 2 warnings`.
- `python3 -m pytest tests/unit/ -q` -> `643 passed, 8 warnings`.
- `python3 -m pyright scout/` -> `0 errors`.
- `ruff check scout/ tests/ scripts/generate_product_demo_gif.py && ruff format --check scout/ tests/ scripts/generate_product_demo_gif.py` -> passed, `228 files already formatted`.
- Playwright Chromium against `scout serve --host 127.0.0.1 --port 8768` -> desktop and mobile loaded the demo headline and `/assets/scout-product-demo.gif`; image natural size was `1280x720`; console messages list was empty.
