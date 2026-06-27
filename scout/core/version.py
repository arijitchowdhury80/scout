"""Scout and Crawl4AI version reporting.

Crawl4AI is read from installed package metadata so /health reflects the
actual runtime dependency loaded in the container. Pin Crawl4AI in
pyproject.toml and upgrade deliberately with regression tests.
"""

from importlib.metadata import PackageNotFoundError, version


def _installed_version(package_name: str) -> str:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "unknown"


CRAWL4AI_VERSION = _installed_version("Crawl4AI")
SCOUT_VERSION = "0.1.1"

UPGRADE_NOTES = """
Crawl4AI upgrade checklist:
- Pin the target Crawl4AI version in pyproject.toml.
- Rebuild the Scout container from docker/docker-compose.yml.
- Verify /health reports the installed package version.
- Check BrowserConfig API for breaking changes.
- Check CrawlerRunConfig parameter renames and new defaults.
- Verify fit_markdown attribute path on CrawlResult.
- Run: pytest tests/ -v && pytest tests/integration/ -v where available.
- Run live smoke tests for /scrape, /crawl, /map, and /screenshot.
"""
