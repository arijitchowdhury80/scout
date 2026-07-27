"""Real PDF extraction — FX-11 Build 1.

Given a PDF URL (or already-fetched PDF bytes), extract text into a
markdown-ish document plus basic metadata (page count, title).

Crawl4AI ships an optional PDF processor
(``crawl4ai.processors.pdf.processor``) but it (a) requires the ``PyPDF2``
extra (``pip install crawl4ai[pdf]``), which is not a Scout dependency, and
(b) is not wired into ``AsyncWebCrawler.arun()`` — there is no supported way
to route a URL through it via the public API. Rather than depend on an
unexposed internal module, this uses ``pypdf`` (BSD-3-Clause, permissive)
directly — already present transitively in this environment and now
declared as an explicit Scout dependency.
"""

from __future__ import annotations

import io

import httpx
import structlog
from pypdf import PdfReader

from scout.core.types import PdfMetadata

logger = structlog.get_logger(__name__)


def looks_like_pdf_url(url: str) -> bool:
    """Cheap extension-based PDF sniff — no network call.

    Strips query string and fragment before checking the suffix, so
    ``https://example.com/report.pdf?download=1`` is still detected.
    """
    path = url.split("?", 1)[0].split("#", 1)[0]
    return path.lower().endswith(".pdf")


def extract_pdf_text(pdf_bytes: bytes) -> tuple[str, PdfMetadata]:
    """Extract text + metadata from raw PDF bytes.

    Returns (markdown, PdfMetadata). Text is joined per-page under a
    "## Page N" heading so downstream consumers get a rough markdown
    document rather than one undifferentiated blob.

    Raises whatever pypdf raises (e.g. ``pypdf.errors.PdfReadError``) if the
    bytes are not a readable PDF — callers are expected to catch this and
    fall back to a failure response rather than let extraction silently
    fabricate content.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))

    encrypted = reader.is_encrypted
    if encrypted:
        # Best-effort empty-password decrypt (common for PDFs that restrict
        # editing/printing but not reading). If this fails we still return
        # accurate page_count/encrypted metadata rather than raising.
        try:
            reader.decrypt("")
        except Exception as exc:  # noqa: BLE001 - pypdf backends raise various errors
            logger.warning("[scout/pdf] decrypt attempt failed", error=str(exc))

    pages_text: list[str] = []
    for page in reader.pages:
        try:
            pages_text.append(page.extract_text() or "")
        except Exception as exc:  # noqa: BLE001 - per-page extraction is best-effort
            logger.warning("[scout/pdf] page extraction failed", error=str(exc))
            pages_text.append("")

    markdown = "\n\n".join(
        f"## Page {index + 1}\n\n{text}".strip() for index, text in enumerate(pages_text)
    )

    title = ""
    try:
        if reader.metadata is not None:
            title = str(reader.metadata.title or "")
    except Exception as exc:  # noqa: BLE001 - metadata dict shape varies across producers
        logger.warning("[scout/pdf] metadata read failed", error=str(exc))

    metadata = PdfMetadata(page_count=len(reader.pages), title=title, encrypted=encrypted)
    return markdown, metadata


async def fetch_pdf_bytes(url: str, *, timeout_ms: int = 30000) -> bytes:
    """Download PDF bytes over plain HTTP — no browser required for a raw file."""
    async with httpx.AsyncClient(timeout=timeout_ms / 1000, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content
