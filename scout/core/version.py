"""Crawl4AI version pin and upgrade notes.

To upgrade Crawl4AI: bump CRAWL4AI_VERSION, run tests, update UPGRADE_NOTES.
Nothing outside this file should import crawl4ai version directly.
"""
CRAWL4AI_VERSION = "0.8.x"
SCOUT_VERSION = "0.1.0"

UPGRADE_NOTES = """
v0.8.x → next:
- Check BrowserConfig API for breaking changes
- Check CrawlerRunConfig parameter renames
- Re-run: pytest tests/ -v
- Update CRAWL4AI_VERSION above
"""
