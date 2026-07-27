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

_SCHEMAS: dict[ExtractionTarget, dict] = {
    "products": _PRODUCT_SCHEMA,
    "executives": _EXECUTIVE_SCHEMA,
}

_ITEM_MODELS: dict[ExtractionTarget, type[BaseModel]] = {
    "products": LLMProductItem,
    "executives": LLMExecutiveItem,
}


async def llm_extract_records(
    content: str,
    target: ExtractionTarget,
    api_key: str,
    *,
    page_url: str = "",
    max_tokens: int = 1500,
) -> list[LLMProductItem] | list[LLMExecutiveItem]:
    """Run the LLM fallback extractor over already-rendered page content.

    Callers must only invoke this after heuristic extraction returned zero
    records for the run (see module docstring) — this function itself does
    not re-check that; it only guards against doing an LLM call with nothing
    to work with (`api_key` or `content` empty).
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
        instruction=_INSTRUCTIONS[target],
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
    max_tokens: int = 1200,
) -> list[LLMExecutiveItem]:
    """Convenience wrapper: LLM fallback for executive records."""
    items = await llm_extract_records(
        content, "executives", api_key, page_url=page_url, max_tokens=max_tokens
    )
    return [item for item in items if isinstance(item, LLMExecutiveItem)]
