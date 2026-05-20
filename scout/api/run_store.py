"""In-memory run registry for frontend artifact lookup."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from scout.core.platform.types import ArtifactFiles, RunManifest


class StoredRun(BaseModel):
    run_id: str
    use_case: str
    output_dir: str
    artifacts: ArtifactFiles


_RUNS: dict[str, StoredRun] = {}


def remember_run(manifest: RunManifest) -> None:
    """Remember a completed run for the current HTTP process."""
    if not manifest.run_id:
        return
    _RUNS[manifest.run_id] = StoredRun(
        run_id=manifest.run_id,
        use_case=manifest.use_case,
        output_dir=manifest.output_dir,
        artifacts=manifest.artifacts,
    )


def get_run(run_id: str) -> StoredRun | None:
    return _RUNS.get(run_id)


def artifact_path(run: StoredRun, artifact_name: str) -> Path:
    value = getattr(run.artifacts, artifact_name)
    return Path(value)
