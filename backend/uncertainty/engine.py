"""Uncertainty Engine for Antarctic Navigation DSS (FR-12, FR-13, FR-14, Phase 9).

Quantifies and combines prediction variances and confidence scores across
sea-ice forecasting, iceberg trajectory prediction, atmospheric/ocean forcing,
and route risk fields.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass
class ConfidenceReport:
    """Confidence status report for a forecast product or route domain."""

    overall_confidence: float  # [0.1, 1.0]
    sea_ice_confidence: float  # [0.1, 1.0]
    iceberg_confidence: float  # [0.1, 1.0]
    forcing_confidence: float  # [0.1, 1.0]
    staleness_hours: float
    horizon_hours: float
    missing_inputs: List[str] = field(default_factory=list)
    provenance_sources: List[str] = field(default_factory=list)
    status_label: str = "HIGH"  # HIGH, MEDIUM, LOW, DEGRADED, STALE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_confidence": float(self.overall_confidence),
            "sea_ice_confidence": float(self.sea_ice_confidence),
            "iceberg_confidence": float(self.iceberg_confidence),
            "forcing_confidence": float(self.forcing_confidence),
            "staleness_hours": float(self.staleness_hours),
            "horizon_hours": float(self.horizon_hours),
            "missing_inputs": list(self.missing_inputs),
            "provenance_sources": list(self.provenance_sources),
            "status_label": self.status_label,
        }


def compute_sic_prediction_interval(sic_pred: Union[float, np.ndarray],
                                    horizon_days: float = 1.0,
                                    confidence_level: float = 0.90) -> Tuple[Any, Any, Any]:
    """Compute empirical prediction interval [lower, upper] and residual std dev for sea ice.

    Empirical residual std dev formula derived from Phase 6 validation runs:
        sigma_sic(h_days) = 0.020 + 0.007 * h_days

    Returns:
        (lower_bound, upper_bound, sigma_sic) clipped to valid concentration fraction [0.0, 1.0].
    """
    sic = np.asarray(sic_pred, dtype=float)
    h = max(1.0, float(horizon_days))

    # Empirical residual standard deviation
    sigma = 0.020 + 0.007 * h

    # Normal distribution z-score (90% -> 1.645, 95% -> 1.960)
    if confidence_level >= 0.95:
        z = 1.960
    elif confidence_level >= 0.90:
        z = 1.645
    else:
        z = 1.000

    margin = z * sigma
    lower = np.clip(sic - margin, 0.0, 1.0)
    upper = np.clip(sic + margin, 0.0, 1.0)

    if np.isscalar(sic_pred):
        return float(lower), float(upper), float(sigma)
    return lower, upper, sigma


def compute_iceberg_uncertainty_ellipse(lon: float,
                                        lat: float,
                                        v_east_kmh: float,
                                        v_north_kmh: float,
                                        horizon_h: float,
                                        obs_staleness_h: float = 0.0) -> Dict[str, Any]:
    """Compute spatial 1-sigma uncertainty radius and ellipse geometry for iceberg trajectory (FR-8, FR-11).

    Uncertainty radius formula:
        sigma_total = sqrt(sigma_base^2 + (sigma_rate * h)^2 + (sigma_stale * tau)^2)
    """
    sigma_base = 0.5  # km fix error
    sigma_rate = 0.12  # km/h horizon growth rate
    sigma_stale = 0.15  # km/h staleness growth rate

    h = max(0.0, float(horizon_h))
    tau = max(0.0, float(obs_staleness_h))

    unc_km = math.sqrt(sigma_base ** 2 + (sigma_rate * h) ** 2 + (sigma_stale * tau) ** 2)

    # Drift heading for anisotropic ellipse orientation
    if abs(v_east_kmh) > 1e-4 or abs(v_north_kmh) > 1e-4:
        heading_deg = math.degrees(math.atan2(v_north_kmh, v_east_kmh)) % 360.0
    else:
        heading_deg = 0.0

    semi_major_km = 1.25 * unc_km
    semi_minor_km = 0.80 * unc_km

    confidence = max(0.10, min(1.0, 1.0 - 0.006 * h - 0.012 * tau))

    return {
        "lon": float(lon),
        "lat": float(lat),
        "horizon_h": float(h),
        "staleness_h": float(tau),
        "uncertainty_km": float(unc_km),
        "semi_major_km": float(semi_major_km),
        "semi_minor_km": float(semi_minor_km),
        "orientation_deg": float(heading_deg),
        "confidence": float(confidence),
    }


def compute_combined_confidence(horizon_h: float = 24.0,
                                staleness_h: float = 0.0,
                                missing_inputs: Optional[List[str]] = None,
                                provenance_sources: Optional[List[str]] = None) -> ConfidenceReport:
    """Compute unified overall confidence score and ConfidenceReport across system outputs (FR-12, FR-13)."""
    h = max(0.0, float(horizon_h))
    tau = max(0.0, float(staleness_h))
    missing = missing_inputs or []
    sources = provenance_sources or ["OSI-SAF", "ERA5", "GLORYS12"]

    # Component confidence scores
    c_ice = max(0.10, min(1.0, 1.0 - 0.005 * h - 0.010 * tau))
    c_berg = max(0.10, min(1.0, 1.0 - 0.006 * h - 0.012 * tau))
    c_forcing = max(0.10, min(1.0, 1.0 - 0.004 * h - 0.008 * tau))

    # Missing input penalty (-0.15 per missing mandatory input)
    penalty = 0.15 * len(missing)

    c_overall = max(0.10, min(1.0, 0.40 * c_ice + 0.35 * c_berg + 0.25 * c_forcing - penalty))

    # Status classification
    if missing:
        status = "DEGRADED"
    elif tau > 24.0:
        status = "STALE"
    elif c_overall >= 0.80:
        status = "HIGH"
    elif c_overall >= 0.55:
        status = "MEDIUM"
    else:
        status = "LOW"

    return ConfidenceReport(
        overall_confidence=float(c_overall),
        sea_ice_confidence=float(c_ice),
        iceberg_confidence=float(c_berg),
        forcing_confidence=float(c_forcing),
        staleness_hours=float(tau),
        horizon_hours=float(h),
        missing_inputs=list(missing),
        provenance_sources=list(sources),
        status_label=status,
    )


def uncertainty_aware_risk(mean_risk: Union[float, np.ndarray],
                          risk_std: Union[float, np.ndarray],
                          risk_aversion_k: float = 1.0) -> Union[float, np.ndarray]:
    """Compute uncertainty-aware risk score inflating perceived risk by variance (FR-14).

    Formula:
        Risk_u_aware = min(1.0, max(0.0, Risk_mean + k * Risk_std))

    Where:
        - k = 0.0: neutral navigator (uses mean risk)
        - k = 1.0: risk-averse navigator (1-sigma inflation)
        - k = 2.0: conservative navigator (2-sigma inflation)
    """
    mr = np.asarray(mean_risk, dtype=float)
    rs = np.asarray(risk_std, dtype=float)
    k = max(0.0, float(risk_aversion_k))

    u_aware = np.clip(mr + k * rs, 0.0, 1.0)

    if np.isscalar(mean_risk) and np.isscalar(risk_std):
        return float(u_aware)
    return u_aware


class UncertaintyEngine:
    """Unified engine managing confidence estimation and uncertainty propagation."""

    def __init__(self, risk_aversion_k: float = 1.0):
        self.risk_aversion_k = risk_aversion_k

    def evaluate_confidence(self,
                            horizon_h: float = 24.0,
                            staleness_h: float = 0.0,
                            missing_inputs: Optional[List[str]] = None,
                            provenance_sources: Optional[List[str]] = None) -> ConfidenceReport:
        """Get unified confidence report."""
        return compute_combined_confidence(horizon_h, staleness_h, missing_inputs, provenance_sources)

    def evaluate_sea_ice_uncertainty(self,
                                     sic_pred: float,
                                     horizon_days: float = 1.0) -> Dict[str, float]:
        """Get sea ice prediction interval and variance."""
        lower, upper, sigma = compute_sic_prediction_interval(sic_pred, horizon_days, confidence_level=0.90)
        return {
            "sic_pred": float(sic_pred),
            "sic_lower_90": float(lower),
            "sic_upper_90": float(upper),
            "sigma_sic": float(sigma),
        }

    def apply_uncertainty_risk_inflation(self,
                                         mean_hazard: Union[float, np.ndarray],
                                         hazard_std: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Apply uncertainty-aware risk inflation rule (FR-14)."""
        return uncertainty_aware_risk(mean_hazard, hazard_std, self.risk_aversion_k)
