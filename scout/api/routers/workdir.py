"""Working-directory browser endpoints for the local Scout frontend."""

import os
import platform
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field


router = APIRouter(tags=["workdir"])


class DirectoryEntry(BaseModel):
    """A directory option visible in the working-directory picker."""

    name: str
    path: str
    is_dir: bool = True


class WorkdirBrowseResponse(BaseModel):
    """Directory listing used by the local output-folder picker."""

    path: str
    parent: str | None
    directories: list[DirectoryEntry] = Field(default_factory=list)


class NativePickerRequest(BaseModel):
    """Request to open the host OS folder picker."""

    current_path: str = "~"


class NativePickerResponse(BaseModel):
    """Native folder picker result."""

    path: str = ""
    picked: bool
    cancelled: bool = False
    reason: str = ""


@router.get("/workdir/browse", response_model=WorkdirBrowseResponse)
async def browse_workdir(path: str = Query(default="~")) -> WorkdirBrowseResponse:
    """Return child directories for a server-local filesystem path."""
    requested = Path(path).expanduser()
    try:
        resolved = requested.resolve()
    except OSError as exc:
        raise HTTPException(status_code=400, detail="Path cannot be resolved") from exc

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="Path does not exist")
    if not resolved.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    directories: list[DirectoryEntry] = []
    try:
        for child in resolved.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                directories.append(DirectoryEntry(name=child.name, path=str(child), is_dir=True))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="Permission denied") from exc

    directories.sort(key=lambda entry: entry.name.lower())
    parent = resolved.parent if resolved.parent != resolved else None
    return WorkdirBrowseResponse(
        path=str(resolved),
        parent=str(parent) if parent is not None else None,
        directories=directories,
    )


@router.post("/workdir/pick-native", response_model=NativePickerResponse)
async def pick_native_workdir(req: NativePickerRequest) -> NativePickerResponse:
    """Open the host OS folder picker and return the selected server-local path."""
    if os.getenv("SCOUT_DISABLE_NATIVE_PICKER") == "1":
        return NativePickerResponse(picked=False, reason="disabled")
    if platform.system() != "Darwin":
        return NativePickerResponse(picked=False, reason="unavailable")

    current = Path(req.current_path or "~").expanduser()
    default_location = current if current.exists() and current.is_dir() else Path.home()
    script = (
        'POSIX path of (choose folder with prompt "Choose where Scout should save run outputs" '
        f'default location POSIX file "{default_location}")'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=408, detail="Native folder picker timed out") from exc

    if result.returncode != 0:
        return NativePickerResponse(picked=False, cancelled=True, reason="cancelled")

    selected = result.stdout.strip()
    if not selected:
        return NativePickerResponse(picked=False, cancelled=True, reason="cancelled")
    return NativePickerResponse(path=selected.rstrip("/"), picked=True)
