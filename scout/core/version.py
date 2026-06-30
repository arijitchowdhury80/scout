"""Runtime version reporting and Crawl4AI upgrade notes.

The health endpoint should report the installed dependency versions, not stale
documentation constants. Keep fallbacks here for editable/source-tree contexts
where package metadata is unavailable.
"""

from __future__ import annotations

from importlib import metadata


def _installed_version(package_name: str, fallback: str) -> str:
    """Return installed package version with a stable fallback."""
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return fallback


CRAWL4AI_VERSION = _installed_version("crawl4ai", "unknown")
SCOUT_VERSION = _installed_version("scout-web", "0.1.0")

UPGRADE_NOTES = """
To upgrade Crawl4AI:
- Check BrowserConfig API for breaking changes
- Check CrawlerRunConfig parameter renames (wait_for, stream flag)
- Verify fit_markdown attribute path on CrawlResult (currently result.markdown.fit_markdown)
- Re-run: pytest tests/ -v && pytest tests/integration/ -v
- Confirm /health reports the installed Crawl4AI version from package metadata
"""
