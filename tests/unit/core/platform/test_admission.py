"""Tests for process-local production admission control."""

from __future__ import annotations

import pytest

from scout.core.platform.admission import AdmissionController, AdmissionRejected


@pytest.mark.asyncio
async def test_admission_controller_rejects_when_capacity_is_full_and_releases() -> None:
    controller = AdmissionController(max_active=1, retry_after_seconds=7)

    async with controller.admit():
        assert controller.active == 1
        with pytest.raises(AdmissionRejected) as exc_info:
            async with controller.admit():
                raise AssertionError("second admission should not enter")

    assert exc_info.value.retry_after_seconds == 7
    assert controller.active == 0

    async with controller.admit():
        assert controller.active == 1
