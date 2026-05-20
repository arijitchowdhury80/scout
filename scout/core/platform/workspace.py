"""Workspace and run-directory resolution for Scout runs."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_WORKDIR = "scout-runs"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "run"


def default_workdir() -> str:
    return os.environ.get("SCOUT_WORKDIR", DEFAULT_WORKDIR)


def resolve_run_output_dir(
    use_case: str,
    query: str = "",
    output_dir: str = "",
    workdir: str = "",
    now: datetime | None = None,
) -> str:
    if output_dir:
        return output_dir

    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    label = slugify("-".join(part for part in [use_case, query] if part))
    base_dir = os.environ.get("SCOUT_WORKDIR") or workdir or DEFAULT_WORKDIR
    return str(Path(base_dir) / f"{label}-{timestamp}")
