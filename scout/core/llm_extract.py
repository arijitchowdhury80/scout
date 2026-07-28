"""LLM extraction fallback for products + executives.

Heuristic-first, cost-bounded: this module is only ever called by a caller
that has already tried the free heuristics (JSON-LD, HTML team/product
cards, browser fallback) and gotten zero records. It never runs on its own
and never fires "just in case" — that discipline lives in the call sites
(scout/core/modes/products.py, scout/core/use_cases/runners/company.py), not
here, but this module still refuses to do anything expensive if handed an
empty api_key or empty content.

Uses the same crawl4ai LLMExtractionStrategy/LLMConfig plumbing as
scout/core/modes/extract.py, pointed at the cheapest capable Anthropic tier
(claude-haiku-4-5) with a bounded max_tokens. Runs against markdown that has
already been rendered/fetched by the caller — no extra browser launch here.

Never fabricates: any model output that doesn't validate against the target
schema is dropped, not guessed at. Any failure (missing key, network error,
garbage JSON) returns an empty list — callers treat that exactly like
"heuristics found nothing" and move on.
"""

from __future__ import annotations

import asyncio
from typing import Literal

import structlog
from crawl4ai import LLMConfig, LLMExtractionStrategy
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger(__name__)

# Cheapest capable Anthropic tier — see ~/.claude/docs (model economics):
# Haiku is the right tier for a bounded, deterministic extraction fallback.
LLM_PROVIDER = "anthropic/claude-haiku-4-5"

# Cap what we send the model. This is a fallback over a single already-fetched
# page, not a full-document summarizer — keeps latency and spend bounded.
_MAX_CONTENT_CHARS = 12000

ExtractionTarget = Literal["products", "executives"]


class LLMProductItem(BaseModel):
    """One product as returned by the LLM fallback. Validated, never trusted blindly."""

    name: str
    price: float | None = None
    currency: str = ""
    url: str = ""


class LLMExecutiveItem(BaseModel):
    """One executive/leader as returned by the LLM fallback."""

    name: str
    title: str = ""


_PRODUCT_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"},
            "currency": {"type": "string"},
            "url": {"type": "string"},
        },
        "required": ["name"],
    },
}

_EXECUTIVE_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "title": {"type": "string"},
        },
        "required": ["name"],
    },
}

_INSTRUCTIONS: dict[ExtractionTarget, str] = {
    "products": (
        "Extract every distinct product listed on this page. Return a JSON list "
        "of objects with exactly these fields: name (string, required), "
        "price (number, no currency symbol, omit the field if no price is shown), "
        "currency (3-letter ISO code such as USD, omit if unknown), "
        "url (the product's own detail-page URL if one appears on the page, "
        "else an empty string). Only include products that are actually named "
        "on the page. If there are no products, return an empty list []. "
        "Never invent a product, price, or URL that isn't on the page."
    ),
    "executives": (
        "Extract every named executive, founder, or leadership team member on "
        "this page. Return a JSON list of objects with exactly these fields: "
        "name (string, required, the person's full name), title (string, their "
        "job title/role such as 'CEO' or 'VP of Engineering', omit if unknown). "
        "Only include people who are actually named on the page. If there are no "
        "named executives, return an empty list []. Never invent a name or title."
    ),
}

# MOAT company-identity guard: appended when the caller knows which company the
# page belongs to. This is what stops the gauntlet's dominant failure —
# returning a DIFFERENT company's CEO (Stripe -> Lightspeed's CEO, Datadog ->
# MongoDB's CEO) or an article author as if they led this company.
_EXECUTIVE_COMPANY_GUARD = (
    " This page belongs to the company '{company}'. Include ONLY the SENIOR "
    "leadership of '{company}' ITSELF: founders, C-level executives (CEO, CFO, "
    "CTO, COO, CMO, CRO, and other 'Chief ... Officer' titles), the president, "
    "EVPs/SVPs, and members of the board of directors. EXCLUDE: middle managers "
    "and narrow-function heads (e.g. 'Head of Product Security', 'Engineering "
    "Manager', 'Sourcing Lead'); article authors and journalists; quoted "
    "customers, partners, or analysts; employees of any OTHER company; and "
    "board members or investors of other firms mentioned only in passing. If you "
    "are not confident a person is senior leadership at '{company}', omit them."
)

_SCHEMAS: dict[ExtractionTarget, dict] = {
    "products": _PRODUCT_SCHEMA,
    "executives": _EXECUTIVE_SCHEMA,
}

_ITEM_MODELS: dict[ExtractionTarget, type[BaseModel]] = {
    "products": LLMProductItem,
    "executives": LLMExecutiveItem,
}


def _instruction_for(target: ExtractionTarget, company: str) -> str:
    """Build the extraction instruction, appending the company-identity guard
    for executives when the caller knows which company the page belongs to."""
    instruction = _INSTRUCTIONS[target]
    if target == "executives" and company.strip():
        instruction += _EXECUTIVE_COMPANY_GUARD.format(company=company.strip())
    return instruction


async def llm_extract_records(
    content: str,
    target: ExtractionTarget,
    api_key: str,
    *,
    page_url: str = "",
    company: str = "",
    max_tokens: int = 1500,
) -> list[LLMProductItem] | list[LLMExecutiveItem]:
    """Run the LLM extractor over already-rendered page content.

    `company`, when given, activates the company-identity guard for executive
    extraction (only return leaders of THIS company). It guards against the
    gauntlet's dominant failure: returning another company's CEO or an article
    author. This function does not re-check the caller's gating; it only guards
    against an LLM call with nothing to work with (`api_key` or `content` empty).
    """
    if not api_key or not content.strip():
        return []

    trimmed = content[:_MAX_CONTENT_CHARS]
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider=LLM_PROVIDER,
            api_token=api_key,
            max_tokens=max_tokens,
            temperature=0,
        ),
        schema=_SCHEMAS[target],
        extraction_type="schema",
        instruction=_instruction_for(target, company),
        input_format="markdown",
        apply_chunking=False,
        verbose=False,
    )

    try:
        blocks = await asyncio.to_thread(strategy.extract, page_url, 0, trimmed)
    except Exception as exc:  # pragma: no cover - defensive, network/library errors
        logger.warning(
            "[scout/llm_extract] LLM call raised", target=target, url=page_url, error=str(exc)
        )
        return []

    if not isinstance(blocks, list):
        return []

    model_cls = _ITEM_MODELS[target]
    items: list = []
    for block in blocks:
        if not isinstance(block, dict) or block.get("error"):
            continue
        try:
            items.append(model_cls.model_validate(block))
        except ValidationError:
            continue

    logger.info(
        "[scout/llm_extract] fallback fired",
        target=target,
        provider=LLM_PROVIDER,
        url=page_url,
        content_chars=len(trimmed),
        items_found=len(items),
    )
    return items


_PAGE_SELECT_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
}

_PAGE_SELECT_TARGETS: dict[str, str] = {
    "leadership": (
        "the page that lists {company}'s OWN executives, founders, leadership, "
        "management team, or board — a team/leadership/about-us/company page"
    ),
    "products": (
        "the page(s) that list {company}'s OWN products for sale or a product "
        "category/catalog listing — not blog, support, or press pages"
    ),
}

# Cap how many candidate links we describe to the model — bounds tokens/cost on
# link-heavy sites (stripe.com exposes ~180 links) while covering the nav/footer.
_MAX_SELECT_CANDIDATES = 60


async def llm_select_pages(
    company: str,
    candidates: list[tuple[str, str]],
    api_key: str,
    *,
    target: str = "leadership",
    limit: int = 3,
    max_tokens: int = 400,
) -> list[str]:
    """Pick the best on-site page(s) for a target from a site's link inventory.

    This is the language- and structure-agnostic replacement for hardcoded URL
    keyword lists: instead of guessing paths or scoring against an English
    keyword set, hand the model the site's ACTUAL links — (anchor_text, url)
    pairs harvested from the rendered nav/footer + sitemap — and let it choose
    which URLs are `{company}`'s leadership/product page.

    Never fabricates a URL: any returned URL not present verbatim in the input
    candidate set is dropped. Returns [] on empty key/candidates or any failure,
    so callers fall back to keyword ranking.
    """
    if not api_key or not candidates:
        return []
    # De-dup by url, preserve order (nav-first), and bound the count sent.
    seen: set[str] = set()
    trimmed: list[tuple[str, str]] = []
    for text, url in candidates:
        if url and url not in seen:
            seen.add(url)
            trimmed.append((text, url))
        if len(trimmed) >= _MAX_SELECT_CANDIDATES:
            break
    valid_urls = {url for _, url in trimmed}
    content = "\n".join(f"- {(text or '(no text)').strip()[:80]} -> {url}" for text, url in trimmed)
    target_desc = _PAGE_SELECT_TARGETS.get(target, _PAGE_SELECT_TARGETS["leadership"]).format(
        company=company.strip() or "the company"
    )
    instruction = (
        f"Below is a list of links (anchor text -> URL) from the website of "
        f"'{company or 'the company'}'. Identify which URLs point to {target_desc}. "
        f"Return a JSON array of objects each with a single field 'url', copied "
        f"EXACTLY from the list, most likely first, at most {limit} items. Only "
        f"choose URLs that appear verbatim in the list above. If none of the "
        f"links point to such a page, return an empty list []."
    )
    strategy = LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider=LLM_PROVIDER, api_token=api_key, max_tokens=max_tokens, temperature=0
        ),
        schema=_PAGE_SELECT_SCHEMA,
        extraction_type="schema",
        instruction=instruction,
        input_format="markdown",
        apply_chunking=False,
        verbose=False,
    )
    try:
        blocks = await asyncio.to_thread(strategy.extract, company or "site", 0, content)
    except Exception as exc:  # pragma: no cover - network/library errors
        logger.warning("[scout/llm_extract] page-select raised", company=company, error=str(exc))
        return []
    if not isinstance(blocks, list):
        return []
    picked: list[str] = []
    for block in blocks:
        if not isinstance(block, dict) or block.get("error"):
            continue
        url = str(block.get("url") or "").strip()
        if url in valid_urls and url not in picked:  # never trust a fabricated URL
            picked.append(url)
        if len(picked) >= limit:
            break
    logger.info(
        "[scout/llm_extract] page-select",
        company=company,
        target=target,
        candidates=len(trimmed),
        picked=len(picked),
    )
    return picked


async def llm_extract_products(
    content: str,
    api_key: str,
    *,
    page_url: str = "",
    max_tokens: int = 1500,
) -> list[LLMProductItem]:
    """Convenience wrapper: LLM fallback for product records."""
    items = await llm_extract_records(
        content, "products", api_key, page_url=page_url, max_tokens=max_tokens
    )
    return [item for item in items if isinstance(item, LLMProductItem)]


async def llm_extract_executives(
    content: str,
    api_key: str,
    *,
    page_url: str = "",
    company: str = "",
    max_tokens: int = 1200,
) -> list[LLMExecutiveItem]:
    """Convenience wrapper: LLM adjudication for executive records.

    Pass `company` to activate the identity guard (only this company's leaders).
    """
    items = await llm_extract_records(
        content, "executives", api_key, page_url=page_url, company=company, max_tokens=max_tokens
    )
    return [item for item in items if isinstance(item, LLMExecutiveItem)]
