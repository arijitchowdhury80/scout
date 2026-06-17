"""Human-assisted acquisition (the in-app/visible-browser rung).

Scout opens a real browser at the target; the human clears any challenge
(press-and-hold, login); Scout polls and, the moment the block detector sees
the page is clear, captures it. Tests use a fake bridge + injected sleep so no
real browser or wall-clock delay is involved.
"""

import asyncio

from scout.core.human_assisted import HumanAssistedOutcome, human_assisted_acquire


class FakeCapture:
    def __init__(self, *, title="", html="", text="", url="https://t/"):
        self.title, self.html, self.text, self.url = title, html, text, url


class FakeBridge:
    """Returns a queue of captures in order; opens are recorded."""

    def __init__(self, captures):
        self._captures = list(captures)
        self.opened = None

    async def open(self, url):
        self.opened = url

    async def capture(self, url):
        # repeat the last capture once the queue is drained
        return self._captures.pop(0) if len(self._captures) > 1 else self._captures[0]


async def _noop_sleep(_seconds):  # injected so tests never actually wait
    return None


def _run(coro):
    return asyncio.run(coro)


def test_cleared_after_human_solves_returns_captured_page() -> None:
    blocked = FakeCapture(title="Just a moment...", html="cf-challenge")
    clear = FakeCapture(title="301 River Glen Dr", html="<h1>home</h1>", text="x" * 400)
    bridge = FakeBridge([blocked, blocked, clear])
    out = _run(human_assisted_acquire("https://zillow/x", bridge, sleep=_noop_sleep))
    assert isinstance(out, HumanAssistedOutcome)
    assert out.status == "cleared"
    assert out.polls == 3
    assert "301 River Glen" in out.title
    assert bridge.opened == "https://zillow/x"


def test_clean_on_first_poll_is_cleared_immediately() -> None:
    clear = FakeCapture(title="Home", html="<h1>hi</h1>", text="y" * 400)
    out = _run(human_assisted_acquire("https://x/", FakeBridge([clear]), sleep=_noop_sleep))
    assert out.status == "cleared"
    assert out.polls == 1


def test_never_cleared_times_out_with_vendor() -> None:
    blocked = FakeCapture(title="", html='<div>geo.captcha-delivery.com datadome</div>')
    out = _run(
        human_assisted_acquire(
            "https://x/", FakeBridge([blocked]), sleep=_noop_sleep,
            poll_interval=1.0, max_wait=3.0,
        )
    )
    assert out.status == "timeout"
    assert out.blocked_vendor == "datadome"


def test_blank_clear_page_is_not_treated_as_cleared() -> None:
    """A non-blocked but near-empty page (intermediate load) is not 'cleared'."""
    thin = FakeCapture(title="", html="<html></html>", text="")
    out = _run(
        human_assisted_acquire(
            "https://x/", FakeBridge([thin]), sleep=_noop_sleep,
            poll_interval=1.0, max_wait=2.0,
        )
    )
    assert out.status == "timeout"
