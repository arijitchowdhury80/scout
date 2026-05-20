from scout.core.platform.execution import (
    ExecutionMode,
    provider_ladder_for_mode,
)
from scout.core.platform.types import FetchProviderKind, RunRequest


def test_run_request_accepts_execution_mode() -> None:
    req = RunRequest(use_case="company", query="Adobe", output_dir="runs/adobe", mode="auto")

    assert req.mode == ExecutionMode.AUTO


def test_auto_mode_provider_ladder_keeps_browser_as_fallback() -> None:
    ladder = provider_ladder_for_mode(ExecutionMode.AUTO)

    assert ladder[:2] == [FetchProviderKind.CRAWL4AI, FetchProviderKind.API]
    assert FetchProviderKind.HOST_BROWSER in ladder
    assert ladder.index(FetchProviderKind.HOST_BROWSER) > ladder.index(FetchProviderKind.CRAWL4AI)


def test_browser_mode_uses_only_browser_provider() -> None:
    assert provider_ladder_for_mode(ExecutionMode.BROWSER) == [FetchProviderKind.HOST_BROWSER]


def test_skill_host_modes_map_to_host_providers() -> None:
    assert provider_ladder_for_mode(ExecutionMode.WEBFETCH) == [FetchProviderKind.HOST_WEBFETCH]
    assert provider_ladder_for_mode(ExecutionMode.WEBSEARCH) == [FetchProviderKind.WEBSEARCH]
