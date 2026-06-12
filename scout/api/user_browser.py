"""Chrome CDP bridge for User Browser capture."""

from __future__ import annotations

import base64
import json
import os
import platform
import socket
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field


CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


class UserBrowserOpenRequest(BaseModel):
    url: str
    run_id: str = ""
    profile_dir: str = ""


class UserBrowserSessionState(BaseModel):
    connected: bool
    status: str
    debugging_port: int | None = None
    profile_dir: str = ""
    chrome_pid: int | None = None
    active_url: str = ""
    title: str = ""
    error: str = ""


class UserBrowserCaptureRequest(BaseModel):
    url: str
    title: str = ""
    html: str
    text: str = ""
    screenshot_data_url: str = ""
    links: list[dict[str, Any]] = Field(default_factory=list)


class ChromeCDPService:
    """Launch and capture from a Scout-managed Chrome CDP session."""

    def __init__(self) -> None:
        self._state = UserBrowserSessionState(connected=False, status="not_started")
        self._process: subprocess.Popen[bytes] | None = None

    async def open_browser(self, req: UserBrowserOpenRequest) -> UserBrowserSessionState:
        if platform.system() != "Darwin":
            self._state = UserBrowserSessionState(
                connected=False,
                status="unsupported_platform",
                active_url=req.url,
                error="User Browser CDP V1 supports macOS only.",
            )
            return self._state
        chrome_path = Path(CHROME_PATH)
        if not chrome_path.exists():
            self._state = UserBrowserSessionState(
                connected=False,
                status="chrome_missing",
                active_url=req.url,
                error=f"Google Chrome not found at {CHROME_PATH}",
            )
            return self._state

        profile_dir = _profile_dir(req.profile_dir)
        profile_dir.mkdir(parents=True, exist_ok=True)

        reusable = self._reusable_state(profile_dir)
        if reusable and reusable.debugging_port:
            self._open_cdp_tab(reusable.debugging_port, req.url)
            self._state = reusable.model_copy(
                update={
                    "connected": True,
                    "status": "opened",
                    "active_url": req.url,
                    "error": "",
                }
            )
            self._save_state(self._state)
            return self._state

        port = _free_port()
        process = subprocess.Popen(
            [
                str(chrome_path),
                f"--remote-debugging-port={port}",
                "--remote-debugging-address=127.0.0.1",
                f"--user-data-dir={profile_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--new-window",
                req.url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._process = process
        if not self._wait_for_cdp(port) or not self._launched_process_is_stable(process, port):
            error = (
                "Chrome launched, but its CDP endpoint was not reachable. "
                "If a Scout Chrome profile is already open, close it and try again."
            )
            self._state = UserBrowserSessionState(
                connected=False,
                status="cdp_unreachable",
                debugging_port=port,
                profile_dir=str(profile_dir),
                chrome_pid=process.pid,
                active_url=req.url,
                error=error,
            )
            self._save_state(self._state)
            return self._state

        self._state = UserBrowserSessionState(
            connected=True,
            status="opened",
            debugging_port=port,
            profile_dir=str(profile_dir),
            chrome_pid=process.pid,
            active_url=req.url,
        )
        self._save_state(self._state)
        return self._state

    async def status(self) -> UserBrowserSessionState:
        if self._state.debugging_port and not self._cdp_reachable(self._state.debugging_port):
            self._state = self._state.model_copy(
                update={
                    "connected": False,
                    "status": "cdp_unreachable",
                    "error": "Chrome CDP endpoint is no longer reachable.",
                }
            )
        return self._state

    async def capture_active_tab(self, target_url: str) -> UserBrowserCaptureRequest:
        if not self._state.debugging_port:
            raise RuntimeError("User Browser Chrome CDP session is not open.")
        if not self._cdp_reachable(self._state.debugging_port):
            self._state = self._state.model_copy(
                update={
                    "connected": False,
                    "status": "cdp_unreachable",
                    "error": "Chrome CDP endpoint is not reachable.",
                }
            )
            raise RuntimeError(
                "Chrome CDP endpoint is not reachable. Close the Scout Chrome window and start a new User Browser run."
            )
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:  # pragma: no cover - dependency boundary
            raise RuntimeError(f"Playwright is not available: {exc}") from exc

        async with async_playwright() as playwright:
            browser = await playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{self._state.debugging_port}"
            )
            pages = [page for context in browser.contexts for page in context.pages]
            if not pages:
                await browser.close()
                raise RuntimeError("No Chrome tabs are available to capture.")
            page = _best_page(pages, target_url)
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=5_000)
            except Exception:
                pass
            title = await page.title()
            html = await page.content()
            text = await page.locator("body").inner_text(timeout=5_000)
            screenshot = await page.screenshot(full_page=True)
            links = await page.eval_on_selector_all(
                "a[href]",
                """anchors => anchors.slice(0, 200).map((a) => ({
                    text: (a.innerText || '').trim().slice(0, 180),
                    href: a.href
                }))""",
            )
            current_url = page.url
            await browser.close()

        self._state.active_url = current_url
        self._state.title = title
        return UserBrowserCaptureRequest(
            url=current_url,
            title=title,
            html=html,
            text=text,
            screenshot_data_url=f"data:image/png;base64,{base64.b64encode(screenshot).decode('ascii')}",
            links=links[:25],
        )

    def _reusable_state(self, profile_dir: Path) -> UserBrowserSessionState | None:
        candidates = [self._state, self._load_state(profile_dir)]
        for candidate in candidates:
            if candidate.debugging_port and self._cdp_reachable(candidate.debugging_port):
                return candidate
        return None

    def _wait_for_cdp(self, port: int, timeout_seconds: float = 4.0) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self._cdp_reachable(port):
                return True
            time.sleep(0.15)
        return False

    def _launched_process_is_stable(self, process: subprocess.Popen[bytes], port: int) -> bool:
        time.sleep(0.75)
        return process.poll() is None and self._cdp_reachable(port)

    def _cdp_reachable(self, port: int) -> bool:
        try:
            data = _cdp_json(port, "/json/version")
        except RuntimeError:
            return False
        return bool(data.get("webSocketDebuggerUrl"))

    def _open_cdp_tab(self, port: int, url: str) -> None:
        try:
            _cdp_json(port, f"/json/new?{quote(url, safe='')}", method="PUT")
        except RuntimeError:
            # Reusing the session is an optimization; if the current tab is already
            # suitable, capture can still proceed from the reachable CDP endpoint.
            pass

    def _save_state(self, state: UserBrowserSessionState) -> None:
        if not state.profile_dir:
            return
        session_path = _session_path(Path(state.profile_dir))
        session_path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def _load_state(self, profile_dir: Path) -> UserBrowserSessionState:
        session_path = _session_path(profile_dir)
        if not session_path.exists():
            return UserBrowserSessionState(connected=False, status="not_started")
        try:
            return UserBrowserSessionState.model_validate_json(
                session_path.read_text(encoding="utf-8")
            )
        except Exception:
            return UserBrowserSessionState(connected=False, status="not_started")


def _profile_dir(profile_dir: str = "") -> Path:
    return Path(
        profile_dir
        or os.getenv("SCOUT_CHROME_PROFILE_DIR", "")
        or "~/.scout/chrome-user-browser-profile"
    ).expanduser()


def _session_path(profile_dir: Path) -> Path:
    return profile_dir / "scout-cdp-session.json"


def _cdp_json(port: int, path: str, *, method: str = "GET") -> dict[str, Any]:
    request = Request(f"http://127.0.0.1:{port}{path}", method=method)
    try:
        with urlopen(request, timeout=1.0) as resp:
            payload = resp.read().decode("utf-8")
    except (OSError, URLError) as exc:
        raise RuntimeError(str(exc)) from exc
    if not payload:
        return {}
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid CDP JSON response: {exc}") from exc
    return data if isinstance(data, dict) else {}


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _best_page(pages: list[Any], target_url: str) -> Any:
    for page in reversed(pages):
        if target_url and page.url.startswith(target_url):
            return page
    for page in reversed(pages):
        if page.url and page.url != "about:blank":
            return page
    return pages[-1]


browser_service = ChromeCDPService()
