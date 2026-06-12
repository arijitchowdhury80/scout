# Acquisition Contract: news

**Consumer:** `algolia-intel-news` (replaces its Apify Google-News actor + newsroom scraping; the skill keeps relevance_signal prose and any judgment beyond deterministic categories).

## Input contract

`url`: newsroom/blog URL or company domain. Option `lookback_days` (default 60). Accepts `targets[]`.

## Acquisition plan

1. Probe `/news`, `/newsroom`, `/press`, `/press-releases`, `/blog`, `/media`, `blog.{domain}` + sitemap matches.
2. **RSS/Atom autodiscovery** on every probed page (`<link rel="alternate">`); feeds preferred over HTML when both exist.
3. Google News RSS (public feed, open-web door): `news.google.com/rss/search?q="{company}"` — replaces the Apify actor.
4. Article listing extraction from HTML when no feed: title, href, date from listing structure.
5. Items within lookback window fetched individually ONLY if the listing lacks dates (cap-bounded).

## Record types & fields

**`news_signal.v1`** (0..n; zero items + documented empty probe set is a valid result)
- title (F — verbatim headline), url (F — **required**), published_at (F: feed date / listing date / article meta)
- source (F: publication or "company newsroom"/"company blog"/"google news rss"), summary (F: feed/listing excerpt, verbatim)
- category_tags[] (T: deterministic keyword categories, same taxonomy the skill uses — LEADERSHIP_CHANGE, FUNDING_EVENT, TECH_INVESTMENT, PRODUCT_LAUNCH, INTERNATIONAL, DIGITAL_INITIATIVE, COMPETITIVE, GENERAL)
- citations[], confidence

Top-level run metadata: `lookback_days`, `collection_date`, feeds_found[], probes_attempted[] (mirrors the consumer's verification-gate keys).

Out of scope (consumer keeps): relevance_signal prose, story selection for the pitch.

## Confidence rules

0.9 item from a feed with a date; 0.8 from newsroom HTML with a parseable date; 0.6 from Google News RSS (third-party aggregation); items without dates capped at 0.5 and flagged.

## Golden e2e flow

Run `news` on `https://constructor.com/blog/` → complete; ≥3 `news_signal.v1` each with title + url + published_at within lookback; every item has ≥1 category tag (GENERAL allowed); run metadata lists the probes and any feeds found.
