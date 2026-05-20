"""Scout platform foundation contracts."""

from scout.core.platform.types import (
    ArtifactFiles,
    Citation,
    FetchProviderKind,
    FetchResult,
    RunRequest,
    RunResponse,
    RunManifest,
    SourceEvidence,
    ValidationFinding,
    ValidationSeverity,
    stable_source_id,
)
from scout.core.platform.targets import (
    TargetMetadata,
    TargetSegment,
    all_targets,
    get_target,
    primary_targets,
    secondary_targets,
    targets_for_use_case,
)

__all__ = [
    "ArtifactFiles",
    "Citation",
    "FetchProviderKind",
    "FetchResult",
    "RunRequest",
    "RunResponse",
    "RunManifest",
    "SourceEvidence",
    "ValidationFinding",
    "ValidationSeverity",
    "stable_source_id",
    "TargetMetadata",
    "TargetSegment",
    "all_targets",
    "get_target",
    "primary_targets",
    "secondary_targets",
    "targets_for_use_case",
]
