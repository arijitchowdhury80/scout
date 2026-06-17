"""Acquisition-ladder T1 stealth wiring: ScrapeRequest knobs must map onto the
right Crawl4AI config objects (read receipt 2026-06-17: proxy/user_agent on
BrowserConfig; override_navigator/simulate_user/magic/mean_delay on
CrawlerRunConfig). Defaults must remain inert so existing callers are unchanged.
"""

from scout.core.modes.scrape import _build_browser_config, _build_run_config
from scout.core.types import ScrapeRequest


def test_defaults_are_inert() -> None:
    req = ScrapeRequest(url="https://example.com")
    bc = _build_browser_config(req)
    rc = _build_run_config(req, want_screenshot=False)
    assert bc.enable_stealth is False
    assert not bc.proxy_config
    assert rc.simulate_user is False
    assert rc.magic is False
    assert rc.override_navigator is False


def test_stealth_flag_enables_browser_and_run_stealth() -> None:
    req = ScrapeRequest(url="https://x.com", stealth=True)
    bc = _build_browser_config(req)
    rc = _build_run_config(req, want_screenshot=False)
    assert bc.enable_stealth is True
    assert rc.simulate_user is True
    assert rc.magic is True
    # stealth runs also get navigator override for free
    assert rc.override_navigator is True


def test_proxy_maps_onto_proxy_config_with_credentials() -> None:
    # Crawl4AI coerces the dict into a ProxyConfig object (read receipt 2026-06-17).
    req = ScrapeRequest(url="https://x.com", proxy="http://u:p@host:8080")
    pc = _build_browser_config(req).proxy_config
    assert pc.server == "http://host:8080"
    assert pc.username == "u"
    assert pc.password == "p"


def test_explicit_user_agent_survives_without_random_mode() -> None:
    req = ScrapeRequest(url="https://x.com", user_agent="CustomUA/1.0")
    assert _build_browser_config(req).user_agent == "CustomUA/1.0"


def test_random_user_agent_mode_generates_a_real_ua() -> None:
    # Crawl4AI regenerates the UA when mode='random' (read receipt 2026-06-17).
    req = ScrapeRequest(url="https://x.com", user_agent_mode="random")
    bc = _build_browser_config(req)
    assert bc.user_agent_mode == "random"
    assert "Mozilla/" in bc.user_agent


def test_override_navigator_and_mean_delay_map_onto_run_config() -> None:
    req = ScrapeRequest(url="https://x.com", override_navigator=True, mean_delay=1.5)
    rc = _build_run_config(req, want_screenshot=False)
    assert rc.override_navigator is True
    assert rc.mean_delay == 1.5


def test_screenshot_flag_threads_through_run_config() -> None:
    req = ScrapeRequest(url="https://x.com")
    assert _build_run_config(req, want_screenshot=True).screenshot is True
    assert _build_run_config(req, want_screenshot=False).screenshot is False
