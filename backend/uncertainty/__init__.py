"""Uncertainty engine module (FR-12, FR-13, FR-14, Phase 9)."""

from .engine import (
    ConfidenceReport,
    UncertaintyEngine,
    compute_combined_confidence,
    compute_iceberg_uncertainty_ellipse,
    compute_sic_prediction_interval,
    uncertainty_aware_risk,
)

__all__ = [
    "ConfidenceReport",
    "UncertaintyEngine",
    "compute_sic_prediction_interval",
    "compute_iceberg_uncertainty_ellipse",
    "compute_combined_confidence",
    "uncertainty_aware_risk",
]
