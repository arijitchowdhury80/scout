from scout.core.version import CRAWL4AI_VERSION, SCOUT_VERSION, UPGRADE_NOTES

def test_versions_are_strings():
    assert isinstance(CRAWL4AI_VERSION, str)
    assert isinstance(SCOUT_VERSION, str)

def test_upgrade_notes_non_empty():
    assert len(UPGRADE_NOTES.strip()) > 0
