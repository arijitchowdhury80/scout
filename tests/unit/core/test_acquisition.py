"""Tests for the acquisition escalation controller (ladder spine, P-spine).

Encodes the human-assisted decision (2026-06-14): automated rungs are tried in
order; on a detected block we escalate; when automated rungs are exhausted and
a human rung exists, the outcome requests a human handoff WITHOUT auto-invoking
it. Every attempt is recorded — certainty of truth, never silent.
"""

import asyncio

from scout.core.acquisition import AcquisitionOutcome, FetchResult, acquire


class FakeRung:
    def __init__(self, name, result=None, requires_human=False, exc=None):
        self.name = name
        self.requires_human = requires_human
        self._result = result
        self._exc = exc
        self.called = False

    async def fetch(self, target: str) -> FetchResult:
        self.called = True
        if self._exc is not None:
            raise self._exc
        assert self._result is not None
        return self._result


def _run(coro):
    return asyncio.run(coro)


def test_first_clean_rung_wins() -> None:
    rung = FakeRung("crawler", FetchResult(status_code=200, title="ok", html="<h1>hi</h1>"))
    out = _run(acquire("http://x", [rung]))
    assert isinstance(out, AcquisitionOutcome)
    assert out.status == "ok"
    assert out.winning_rung == "crawler"
    assert out.result is not None and "hi" in out.result.html


def test_blocked_then_clean_escalates() -> None:
    blocked = FakeRung("crawler", FetchResult(status_code=403, title="Just a moment", html="cf-challenge"))
    clean = FakeRung("undetected", FetchResult(status_code=200, title="ok", html="<h1>hi</h1>"))
    out = _run(acquire("http://x", [blocked, clean]))
    assert out.status == "ok"
    assert out.winning_rung == "undetected"
    assert len(out.attempts) == 2
    assert out.attempts[0].blocked is True
    assert out.attempts[0].vendor == "cloudflare"
    assert out.attempts[1].ok is True


def test_all_blocked_with_human_rung_requests_handoff_without_calling_it() -> None:
    b1 = FakeRung("crawler", FetchResult(status_code=200, html='<script src="geo.captcha-delivery.com"></script>'))
    human = FakeRung("user-browser", requires_human=True)
    out = _run(acquire("http://x", [b1, human]))
    assert out.status == "blocked_needs_human"
    assert out.human_rung == "user-browser"
    assert human.called is False  # the human rung must never be auto-invoked


def test_rung_failure_is_recorded_and_escalates() -> None:
    boom = FakeRung("crawler", exc=RuntimeError("net down"))
    clean = FakeRung("undetected", FetchResult(status_code=200, html="<h1>hi</h1>"))
    out = _run(acquire("http://x", [boom, clean]))
    assert out.status == "ok"
    assert out.attempts[0].ok is False
    assert out.attempts[0].blocked is False
    assert "net down" in out.attempts[0].note


def test_all_automated_blocked_no_human_is_exhausted() -> None:
    b1 = FakeRung("crawler", FetchResult(status_code=403, title="Just a moment", html="cf"))
    out = _run(acquire("http://x", [b1]))
    assert out.status == "blocked_exhausted"
    assert out.winning_rung is None
    assert out.human_rung is None
