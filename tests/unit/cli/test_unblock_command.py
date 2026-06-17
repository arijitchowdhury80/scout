"""The `scout unblock` glue: the CDP bridge adapter must delegate open/capture
to the injected service (so the engine flow stays decoupled from the api layer),
and the command must be registered.
"""

import asyncio

from scout.cli import _CDPBridge, app


class FakeService:
    def __init__(self) -> None:
        self.opened_url = None
        self.captured_url = None

    async def open_browser(self, req):
        self.opened_url = req.url
        return None

    async def capture_active_tab(self, url):
        self.captured_url = url
        return object()


def test_bridge_open_delegates_with_url() -> None:
    svc = FakeService()
    asyncio.run(_CDPBridge(svc).open("https://zillow.com/x"))
    assert svc.opened_url == "https://zillow.com/x"


def test_bridge_capture_delegates_with_url() -> None:
    svc = FakeService()
    asyncio.run(_CDPBridge(svc).capture("https://zillow.com/x"))
    assert svc.captured_url == "https://zillow.com/x"


def test_unblock_command_is_registered() -> None:
    names = {c.name or c.callback.__name__ for c in app.registered_commands}
    assert "unblock" in names
