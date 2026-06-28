"""Feature certification helpers for Scout release validation."""

from .certification import (
    REQUIRED_FEATURE_AREAS,
    FEATURE_CERTIFICATION_MATRIX,
    CertificationActual,
    CertificationOutputs,
    CertificationResult,
    CertificationScenario,
    certification_actual_from_dict,
    certification_results_from_evidence,
    certify_actual,
    load_certification_evidence,
    write_certification_outputs,
)
from .evidence_generator import EvidenceGenerationResult, generate_service_certification_evidence

__all__ = [
    "REQUIRED_FEATURE_AREAS",
    "FEATURE_CERTIFICATION_MATRIX",
    "CertificationActual",
    "CertificationOutputs",
    "CertificationResult",
    "CertificationScenario",
    "certification_actual_from_dict",
    "certification_results_from_evidence",
    "certify_actual",
    "load_certification_evidence",
    "write_certification_outputs",
    "EvidenceGenerationResult",
    "generate_service_certification_evidence",
]
