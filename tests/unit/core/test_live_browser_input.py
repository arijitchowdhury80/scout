"""Input forwarding for the embedded browser: UI canvas events (mouse/keyboard
from the Scout web UI) must map to the exact CDP Input.* commands so a human's
clicks/keys in the embedded pane reach the real browser. Pure mapping — no
browser needed.

Open question this enables testing later: whether CDP-forwarded input (vs native
OS input) clears behavioral challenges like PerimeterX press-and-hold.
"""

import pytest

from scout.core.live_browser import input_event_to_cdp


def test_mousemove_maps_to_mouse_moved() -> None:
    method, params = input_event_to_cdp({"type": "mousemove", "x": 10, "y": 20})
    assert method == "Input.dispatchMouseEvent"
    assert params["type"] == "mouseMoved"
    assert params["x"] == 10 and params["y"] == 20


def test_mousedown_and_up_map_with_button_and_clickcount() -> None:
    m_down, p_down = input_event_to_cdp({"type": "mousedown", "x": 5, "y": 6, "button": "left"})
    assert p_down["type"] == "mousePressed"
    assert p_down["button"] == "left"
    assert p_down["clickCount"] == 1
    _, p_up = input_event_to_cdp({"type": "mouseup", "x": 5, "y": 6, "button": "left"})
    assert p_up["type"] == "mouseReleased"


def test_wheel_maps_to_mouse_wheel_with_deltas() -> None:
    method, params = input_event_to_cdp(
        {"type": "wheel", "x": 1, "y": 2, "deltaX": 0, "deltaY": 120}
    )
    assert method == "Input.dispatchMouseEvent"
    assert params["type"] == "mouseWheel"
    assert params["deltaY"] == 120


def test_keydown_carries_key_and_text() -> None:
    method, params = input_event_to_cdp({"type": "keydown", "key": "a", "text": "a"})
    assert method == "Input.dispatchKeyEvent"
    assert params["type"] == "keyDown"
    assert params["key"] == "a"
    assert params["text"] == "a"


def test_keyup_maps_to_key_up() -> None:
    _, params = input_event_to_cdp({"type": "keyup", "key": "Enter"})
    assert params["type"] == "keyUp"
    assert params["key"] == "Enter"


def test_unknown_event_type_raises() -> None:
    with pytest.raises(ValueError):
        input_event_to_cdp({"type": "teleport", "x": 0, "y": 0})


# --- URL normalization (live finding 2026-06-18: bare domain failed goto) ---


def test_bare_domain_gets_https() -> None:
    from scout.core.live_browser import normalize_url

    assert normalize_url("algolia.com") == "https://algolia.com"
    assert normalize_url("  zillow.com/x ") == "https://zillow.com/x"


def test_existing_scheme_is_preserved() -> None:
    from scout.core.live_browser import normalize_url

    assert normalize_url("https://x.com") == "https://x.com"
    assert normalize_url("http://x.com") == "http://x.com"
    assert normalize_url("about:blank") == "about:blank"


def test_empty_url_becomes_about_blank() -> None:
    from scout.core.live_browser import normalize_url

    assert normalize_url("") == "about:blank"
    assert normalize_url("   ") == "about:blank"
