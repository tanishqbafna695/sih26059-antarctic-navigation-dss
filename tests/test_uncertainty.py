"""Unit tests for Phase 9 Uncertainty Engine (FR-12, FR-13, FR-14)."""

import numpy as np
import pytest

from backend.uncertainty import (
    ConfidenceReport,
    UncertaintyEngine,
    compute_combined_confidence,
    compute_iceberg_uncertainty_ellipse,
    compute_sic_prediction_interval,
    uncertainty_aware_risk,
)


def test_sea_ice_prediction_interval_grows_with_horizon():
    low1, upp1, sig1 = compute_sic_prediction_interval(0.50, horizon_days=1.0)
    low5, upp5, sig5 = compute_sic_prediction_interval(0.50, horizon_days=5.0)

    assert sig5 > sig1
    assert (upp5 - low5) > (upp1 - low1)


def test_sea_ice_prediction_interval_clipping_bounds():
    # Near boundaries (0.05 and 0.95), interval must stay inside [0.0, 1.0]
    low_bound, upp_bound, _ = compute_sic_prediction_interval(0.02, horizon_days=5.0, confidence_level=0.95)
    assert low_bound == pytest.approx(0.0)
    assert upp_bound > 0.02

    low_bound2, upp_bound2, _ = compute_sic_prediction_interval(0.98, horizon_days=5.0, confidence_level=0.95)
    assert upp_bound2 == pytest.approx(1.0)
    assert low_bound2 < 0.98


def test_iceberg_uncertainty_ellipse_expansion():
    ell_24 = compute_iceberg_uncertainty_ellipse(60.0, -68.0, 1.0, 0.5, horizon_h=24.0, obs_staleness_h=0.0)
    ell_72 = compute_iceberg_uncertainty_ellipse(60.0, -68.0, 1.0, 0.5, horizon_h=72.0, obs_staleness_h=0.0)
    ell_stale = compute_iceberg_uncertainty_ellipse(60.0, -68.0, 1.0, 0.5, horizon_h=72.0, obs_staleness_h=24.0)

    assert ell_72["uncertainty_km"] > ell_24["uncertainty_km"]
    assert ell_stale["uncertainty_km"] > ell_72["uncertainty_km"]
    assert ell_stale["confidence"] < ell_72["confidence"]


def test_confidence_degradation_with_staleness_and_missingness():
    c_norm = compute_combined_confidence(horizon_h=24.0, staleness_h=0.0)
    c_stale = compute_combined_confidence(horizon_h=24.0, staleness_h=24.0)
    c_missing = compute_combined_confidence(horizon_h=24.0, staleness_h=0.0, missing_inputs=["sic"])

    assert c_stale.overall_confidence < c_norm.overall_confidence
    assert c_missing.overall_confidence < c_norm.overall_confidence
    assert c_missing.status_label in ("DEGRADED", "LOW")


def test_uncertainty_aware_risk_inflation_fr14():
    mean_risk = 0.40
    risk_std = 0.15

    r_k0 = uncertainty_aware_risk(mean_risk, risk_std, risk_aversion_k=0.0)
    r_k1 = uncertainty_aware_risk(mean_risk, risk_std, risk_aversion_k=1.0)
    r_k2 = uncertainty_aware_risk(mean_risk, risk_std, risk_aversion_k=2.0)

    assert r_k0 == pytest.approx(0.40)
    assert r_k1 == pytest.approx(0.55)
    assert r_k2 == pytest.approx(0.70)

    # Capped at 1.0
    r_capped = uncertainty_aware_risk(0.80, 0.30, risk_aversion_k=2.0)
    assert r_capped == pytest.approx(1.0)


def test_uncertainty_engine_class():
    engine = UncertaintyEngine(risk_aversion_k=1.5)
    report = engine.evaluate_confidence(horizon_h=24.0)

    assert isinstance(report, ConfidenceReport)
    assert report.overall_confidence > 0.0

    sic_unc = engine.evaluate_sea_ice_uncertainty(0.60, horizon_days=3.0)
    assert sic_unc["sic_lower_90"] < 0.60 < sic_unc["sic_upper_90"]

    r_inflated = engine.apply_uncertainty_risk_inflation(0.50, 0.10)
    assert r_inflated == pytest.approx(0.65)
