# Acquisition Contract: research (narrowed per boundary ADR)

**Was:** "normalize broad web research" — failed the boundary test (open-ended synthesis).
**Now:** fetch + extract from a GIVEN set of URLs. The consumer decides what to read; Scout reads it well.

## Input contract
`targets[]`: explicit URL list (1..N). Option `extract` (css-schema or none).

## Acquisition plan
Fetch each URL through the ladder; extract clean markdown + metadata; optional structured extraction via existing CSS-schema extract mode. No discovery, no search, no link-following.

## Record types & fields
**`research_page.v1`** per URL — url (F), title (F), markdown (F: clean content), word_count (F), fetched_at (F), extract (F: schema results when requested), keyword_tags[] (T: only when `topic_tags` provided in input), citations[], confidence.

Out of scope: summarization, synthesis across pages, answering questions. (LLM summary was considered and rejected — it is interpretation; consumers summarize.)

## Confidence rules
0.9 direct fetch; 0.7 via browser fallback (flagged); blocked → BlockedPage, no record.

## Golden e2e flow
Run `research` with 3 known URLs → complete; 3 `research_page.v1` with non-empty markdown whose first heading matches the live page; 0 records for any blocked URL with matching BlockedPage evidence.
