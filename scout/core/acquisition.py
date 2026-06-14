"""Acquisition escalation controller — the spine of Scout's unblock ladder.

Tries acquisition rungs in order (cheap → strong). After each automated rung it
runs block detection (`scout.core.blocking`); on a block it escalates to the
next rung. When the automated rungs are exhausted and a human rung exists
(the user's real browser, where a person clears a press-and-hold / login once),
the outcome requests a human handoff — it NEVER auto-invokes the human rung.

Design principle (ADR 2026-06-14): certainty of truth. Every attempt is
recorded with what happened and why; nothing is silently dropped or faked.
"""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from pydantic import BaseModel

from scout.core.blocking import detect_block


class FetchResult(BaseModel):
    """What a single rung returns from one fetch attempt."""

    status_code: int | None = None
    title: str = ""
    html: str = ""
    markdown: str = ""
    final_url: str = ""


@runtime_checkable
class AcquisitionRung(Protocol):
    """A rung in the ladder. `requires_human=True` rungs are never auto-run."""

    name: str
    requires_human: bool

    async def fetch(self, target: str) -> FetchResult: ...


class AcquisitionAttempt(BaseModel):
    """Honest record of one rung attempt."""

    model_config = {"frozen": True}

    rung: str
    ok: bool
    blocked: bool = False
    vendor: str = "none"
    note: str = ""


AcquisitionStatus = Literal["ok", "blocked_needs_human", "blocked_exhausted"]


class AcquisitionOutcome(BaseModel):
    """Result of climbing the ladder. `status` is the honest verdict."""

    status: AcquisitionStatus
    winning_rung: str | None = None
    human_rung: str | None = None
    attempts: list[AcquisitionAttempt] = []
    result: FetchResult | None = None


async def acquire(target: str, rungs: list[AcquisitionRung]) -> AcquisitionOutcome:
    """Climb the ladder for `target`, escalating on blocks.

    Returns the first non-blocked rung's content as `ok`; otherwise
    `blocked_needs_human` (naming the human rung, which is not invoked) if one
    is registered, else `blocked_exhausted`.
    """
    attempts: list[AcquisitionAttempt] = []
    human_rung: str | None = None

    for rung in rungs:
        if getattr(rung, "requires_human", False):
            # Register the human backstop but never auto-run it.
            human_rung = rung.name
            continue

        try:
            res = await rung.fetch(target)
        except Exception as exc:  # noqa: BLE001 — record and escalate, never crash the ladder
            attempts.append(
                AcquisitionAttempt(rung=rung.name, ok=False, note=f"error: {exc}")
            )
            continue

        signal = detect_block(
            res.status_code, title=res.title, html=res.html, markdown=res.markdown
        )
        if signal.blocked:
            attempts.append(
                AcquisitionAttempt(
                    rung=rung.name,
                    ok=False,
                    blocked=True,
                    vendor=signal.vendor,
                    note=signal.reason,
                )
            )
            continue

        attempts.append(AcquisitionAttempt(rung=rung.name, ok=True))
        return AcquisitionOutcome(
            status="ok",
            winning_rung=rung.name,
            human_rung=human_rung,
            attempts=attempts,
            result=res,
        )

    status: AcquisitionStatus = (
        "blocked_needs_human" if human_rung else "blocked_exhausted"
    )
    return AcquisitionOutcome(status=status, human_rung=human_rung, attempts=attempts)
