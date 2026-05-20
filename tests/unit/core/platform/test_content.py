from scout.core.platform.content import fetch_result_from_markdown
from scout.core.platform.types import FetchProviderKind


def test_fetch_result_from_markdown() -> None:
    result = fetch_result_from_markdown(
        markdown="# About Example",
        source_url="https://example.com/about",
        provider=FetchProviderKind.SAVED,
        fetched_at="2026-05-15T12:00:00Z",
    )

    assert result.markdown == "# About Example"
    assert result.text == "# About Example"
    assert result.evidence.source_url == "https://example.com/about"
    assert result.evidence.final_url == "https://example.com/about"
    assert result.evidence.provider == FetchProviderKind.SAVED
