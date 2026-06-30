from importlib import metadata

from scout.core.version import CRAWL4AI_VERSION, SCOUT_VERSION, UPGRADE_NOTES, _installed_version


def test_versions_are_strings():
    assert isinstance(CRAWL4AI_VERSION, str)
    assert isinstance(SCOUT_VERSION, str)


def test_upgrade_notes_non_empty():
    assert len(UPGRADE_NOTES.strip()) > 0


def test_installed_version_uses_metadata_when_available(monkeypatch):
    def fake_version(package_name: str) -> str:
        assert package_name == "crawl4ai"
        return "9.9.9"

    monkeypatch.setattr("scout.core.version.metadata.version", fake_version)

    assert _installed_version("crawl4ai", "fallback") == "9.9.9"


def test_installed_version_falls_back_when_metadata_missing(monkeypatch):
    def fake_version(package_name: str) -> str:
        raise metadata.PackageNotFoundError(package_name)

    monkeypatch.setattr("scout.core.version.metadata.version", fake_version)

    assert _installed_version("missing", "fallback") == "fallback"
