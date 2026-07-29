"""Scout core types — the contract every endpoint fulfils.

All request/response models are defined here. Nothing outside this file
defines the API contract. Change here first; implementations follow.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ScoutFormats(str, Enum):
    MARKDOWN = "markdown"
    RAW_HTML = "raw_html"
    SCREENSHOT = "screenshot"


class ScoutMetadata(BaseModel):
    model_config = {"frozen": True}

    url: str
    crawled_at: str
    title: str = ""
    description: str = ""
    language: str = ""
    word_count: int = 0
    token_estimate: int = 0


# ---------------------------------------------------------------------------
# /scrape
# ---------------------------------------------------------------------------


class ScrapeRequest(BaseModel):
    url: str
    formats: list[ScoutFormats] = [ScoutFormats.MARKDOWN]
    use_js: bool = False
    wait_for: str = ""
    timeout_ms: int = 30000
    stealth: bool = False  # enable_stealth + simulate_user + magic in Crawl4AI
    headless: bool = True
    # --- acquisition-ladder stealth knobs (T1 rung); all opt-in, defaults inert ---
    proxy: str | None = None  # e.g. "http://user:pass@host:port" → Crawl4AI BrowserConfig.proxy
    user_agent: str | None = None  # explicit UA; overrides default
    user_agent_mode: str | None = None  # "random" rotates a realistic UA per run
    override_navigator: bool = False  # patch navigator.* to defeat headless fingerprinting
    mean_delay: float | None = None  # human-like pacing between actions (seconds)
    # FX-10a: respect robots.txt by default (maps to CrawlerRunConfig.check_robots_txt,
    # which crawl4ai itself defaults to False). Explicit False opts out.
    respect_robots_txt: bool = True
    # --- MOAT: intelligence-render knobs (the exec/product moat depends on the
    # RIGHT page being FULLY rendered before extraction). All opt-in; defaults
    # keep crawl4ai's own behaviour so existing callers render unchanged.
    # Map onto crawl4ai 0.7.7 CrawlerRunConfig (read receipt 2026-07-27).
    scan_full_page: bool = False  # scroll page to flush lazy-loaded team/product content
    wait_until: str = ""  # "" keeps crawl4ai default (domcontentloaded); e.g. "networkidle"
    delay_before_return_html: float | None = None  # seconds to let client-side hydration paint
    block_images: bool = False  # drop images (exclude_all + external) for speed on ad-heavy pages


class PdfMetadata(BaseModel):
    """Metadata extracted from a PDF document (FX-11 Build 1).

    Populated only when ScrapeResponse.provider == "pdf" — i.e. the scraped
    URL resolved to a PDF byte stream and was routed through the pypdf
    extraction path instead of Crawl4AI's browser pipeline.
    """

    model_config = {"frozen": True}

    page_count: int = 0
    title: str = ""
    encrypted: bool = False


class ScrapeResponse(BaseModel):
    success: bool
    url: str
    status_code: int | None = None
    markdown: str = ""
    raw_markdown: str = ""
    clean_markdown: str = ""
    raw_html: str = ""
    screenshot_base64: str = ""
    links: list[str] = Field(default_factory=list)
    metadata: ScoutMetadata
    final_url: str = ""
    fetched_at: str = ""
    provider: str = ""
    content_hash: str = ""
    cleanup_rules_applied: list[str] = Field(default_factory=list)
    quality_score: float = 0.0
    quality_reasons: list[str] = Field(default_factory=list)
    recommended_collector: str = ""
    recommended_collector_reason: str = ""
    error: str = ""
    duration_ms: int
    pdf: PdfMetadata | None = None


# ---------------------------------------------------------------------------
# /crawl
# ---------------------------------------------------------------------------


class CrawlRequest(BaseModel):
    url: str
    max_depth: int = 2
    max_pages: int = 10
    url_pattern: str = ""
    include_external: bool = False
    use_js: bool = False
    timeout_ms: int = 60000
    stealth: bool = False
    # FX-10a: respect robots.txt by default (maps to CrawlerRunConfig.check_robots_txt).
    respect_robots_txt: bool = True


class CrawlPage(BaseModel):
    url: str
    markdown: str = ""
    metadata: ScoutMetadata
    success: bool
    error: str = ""


class CrawlResponse(BaseModel):
    success: bool
    start_url: str
    pages: list[CrawlPage] = Field(default_factory=list)
    total_pages: int
    error: str = ""
    duration_ms: int


# ---------------------------------------------------------------------------
# /extract
# ---------------------------------------------------------------------------


class ExtractRequest(BaseModel):
    model_config = {"populate_by_name": True}

    url: str
    extraction_schema: dict = Field(default_factory=dict, alias="schema")
    instruction: str = ""
    llm_provider: str = "ollama/llama3.2:3b"
    css_schema: dict | None = None  # {baseSelector, fields: [{name, selector, type}]}
    use_js: bool = False
    timeout_ms: int = 45000


class ExtractResponse(BaseModel):
    success: bool
    url: str
    data: dict = Field(default_factory=dict)
    markdown: str = ""
    metadata: ScoutMetadata
    error: str = ""
    duration_ms: int


# ---------------------------------------------------------------------------
# Capture structuring
#
# Turn an already-fetched page (e.g. a human-cleared native-browser grab) into
# clean markdown + optional typed records WITHOUT re-fetching. Re-fetching a
# cleared page would re-trigger the anti-bot wall the human just solved, so the
# captured HTML is run through Crawl4AI via the `raw://` scheme instead.
# ---------------------------------------------------------------------------


class CaptureExtraction(BaseModel):
    success: bool
    source_url: str = ""
    markdown: str = ""  # clean filtered markdown (always populated on success)
    raw_html: str = ""  # held/captured HTML, used for no-refetch productization paths
    records: list[dict] = Field(default_factory=list)  # typed records iff a schema was given
    record_count: int = 0
    word_count: int = 0
    error: str = ""
    duration_ms: int = 0


# ---------------------------------------------------------------------------
# /map
# ---------------------------------------------------------------------------


class MapRequest(BaseModel):
    url: str
    max_pages: int = 100
    url_pattern: str = ""
    include_external: bool = False
    stealth: bool = False


class MapResponse(BaseModel):
    success: bool
    start_url: str
    urls: list[str] = Field(default_factory=list)
    total: int
    error: str = ""
    duration_ms: int


# ---------------------------------------------------------------------------
# /screenshot
# ---------------------------------------------------------------------------


class ScreenshotRequest(BaseModel):
    url: str
    full_page: bool = True
    viewport_width: int = 1280
    viewport_height: int = 800
    wait_for: str = ""
    use_js: bool = True


class ScreenshotResponse(BaseModel):
    success: bool
    url: str
    screenshot_base64: str = ""
    width: int
    height: int
    error: str = ""
    duration_ms: int


# ---------------------------------------------------------------------------
# /products
# ---------------------------------------------------------------------------


class ProductCrawlRequest(BaseModel):
    query: str = ""
    site: str = ""
    start_url: str = ""
    limit_per_category: int = 10
    max_categories: int = 10
    max_products: int = 100
    output_dir: str = ""
    persist: bool = False
    use_js: bool = True
    timeout_ms: int = 60000
    stealth: bool = False
    browser_fallback: bool = True
    # FX-1: the hosted container has no X server / $DISPLAY. A headed
    # ("browser_fallback_headless=False") launch crashes with
    # "Missing X server or $DISPLAY" (the eyebuydirect repro). Default to
    # headless so any caller that doesn't explicitly opt into a visible
    # browser (e.g. the CLI, run by a human on their own machine) gets a
    # fallback that actually works in the hosted/products context.
    browser_fallback_headless: bool = True
    # FX-10a: respect robots.txt by default for every fetch this crawl issues.
    respect_robots_txt: bool = True


class ProductSource(BaseModel):
    url: str
    extractor: str
    category_url: str = ""
    category_name: str = ""


class ProductListingCard(BaseModel):
    url: str
    name: str = ""
    brand: str = ""
    image: str = ""
    price: float | None = None
    currency: str = ""
    category_url: str = ""
    category_name: str = ""


class BlockedPage(BaseModel):
    url: str
    reason: str
    category_url: str = ""
    category_name: str = ""
    title: str = ""
    fallback_attempted: bool = False
    fallback_used: bool = False
    fallback_error: str = ""


class ProductVariant(BaseModel):
    sku: str = ""
    name: str = ""
    price: float | None = None
    currency: str = ""
    color: str = ""
    size: str = ""
    in_stock: bool | None = None


class AlgoliaProductRecord(BaseModel):
    model_config = {"populate_by_name": True}

    objectID: str
    name: str
    url: str
    brand: str = ""
    description: str = ""
    image: str = ""
    images: list[str] = Field(default_factory=list)
    price: float | None = None
    currency: str = ""
    categories: list[str] = Field(default_factory=list)
    hierarchicalCategories: dict[str, str] = Field(default_factory=dict)
    sku: str = ""
    variants: list[ProductVariant] = Field(default_factory=list)
    in_stock: bool | None = None
    source: ProductSource = Field(serialization_alias="_source")
    citations: list[dict[str, object]] = Field(default_factory=list)
    completeness_score: float = 0.0


class ProductArtifactFiles(BaseModel):
    manifest: str = ""
    urls: str = ""
    raw_products: str = ""
    products_json: str = ""
    products_ndjson: str = ""
    settings_json: str = ""
    blocked_pages_json: str = ""
    report: str = ""


class ProductCrawlResponse(BaseModel):
    success: bool
    query: str = ""
    site: str = ""
    start_url: str = ""
    output_dir: str = ""
    records: list[AlgoliaProductRecord] = Field(default_factory=list)
    total_records: int
    categories: list[str] = Field(default_factory=list)
    blocked_pages: list[BlockedPage] = Field(default_factory=list)
    total_blocked_pages: int = 0
    files: ProductArtifactFiles = Field(default_factory=ProductArtifactFiles)
    error: str = ""
    duration_ms: int
