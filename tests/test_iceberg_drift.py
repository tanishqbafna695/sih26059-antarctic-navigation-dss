"""Unit tests for Phase 7 iceberg trajectory prediction models (FR-8, FR-9, FR-10, FR-11)."""

import math

import numpy as np
import pandas as pd
import pytest

from backend.iceberg import (
    IcebergMLDriftModel,
    IcebergPhysicsDriftModel,
    evaluate_iceberg_models,
)
from backend.iceberg.drift import _estimate_kinematic_velocity, _rotate_wind_vector


def test_wind_deflection_rotation_southern_hemisphere():
    # Pure eastward wind (u=10, v=0) rotated by -20 deg leftward
    u_rot, v_rot = _rotate_wind_vector(10.0, 0.0, deflection_deg=-20.0)
    assert u_rot == pytest.approx(10.0 * math.cos(math.radians(-20.0)))
    assert v_rot == pytest.approx(10.0 * math.sin(math.radians(-20.0)))
    assert v_rot < 0.0  # leftward deflection in Southern Hemisphere yields southward component


def test_physics_drift_model_momentum_decay():
    model = IcebergPhysicsDriftModel(momentum_decay_h=24.0)

    # 10 km/h initial velocity east, zero forcing
    ve_24, vn_24 = model.predict_drift_velocity(10.0, 0.0, horizon_h=24.0)
    ve_72, vn_72 = model.predict_drift_velocity(10.0, 0.0, horizon_h=72.0)

    # Velocity at 72h should be smaller than at 24h due to momentum decay
    assert ve_72 < ve_24
    assert ve_24 == pytest.approx(10.0 * math.exp(-1.0), rel=1e-2)


def test_uncertainty_growth_with_horizon_and_staleness():
    model = IcebergPhysicsDriftModel()

    res_24 = model.predict_position(60.0, -68.0, 1.0, 0.0, horizon_h=24.0, obs_staleness_h=0.0)
    res_72 = model.predict_position(60.0, -68.0, 1.0, 0.0, horizon_h=72.0, obs_staleness_h=0.0)
    res_72_stale = model.predict_position(60.0, -68.0, 1.0, 0.0, horizon_h=72.0, obs_staleness_h=12.0)

    assert res_72["uncertainty_km"] > res_24["uncertainty_km"]
    assert res_72_stale["uncertainty_km"] > res_72["uncertainty_km"]
    assert res_72["confidence"] < res_24["confidence"]
    assert res_72_stale["confidence"] < res_72["confidence"]


def test_ml_drift_model_fallback_when_unfitted():
    ml_model = IcebergMLDriftModel()

    res_ml = ml_model.predict_position(60.0, -68.0, 1.0, 0.5, horizon_h=24.0)
    res_phys = ml_model.physics_fallback.predict_position(60.0, -68.0, 1.0, 0.5, horizon_h=24.0)

    assert res_ml["lon"] == pytest.approx(res_phys["lon"])
    assert res_ml["lat"] == pytest.approx(res_phys["lat"])


def test_ml_drift_model_fit_and_predict():
    # Build synthetic track with 5 fixes
    rows = []
    for i in range(6):
        rows.append({
            "berg_id": "B_TEST",
            "time": pd.Timestamp("2019-12-01") + pd.Timedelta(hours=i * 24),
            "lon": 60.0 + 0.1 * i + 0.01 * i * i,
            "lat": -68.0 + 0.05 * i,
            "source": "synthetic"
        })
    df = pd.DataFrame(rows)

    ml_model = IcebergMLDriftModel()
    ml_model.fit(df)
    assert ml_model.is_fitted

    pred = ml_model.predict_position(60.5, -67.8, 0.5, 0.2, horizon_h=24.0)
    assert "lon" in pred and "lat" in pred
    assert pred["uncertainty_km"] > 0.0


def test_evaluate_iceberg_models_end_to_end():
    rows = []
    for i in range(5):
        rows.append({
            "berg_id": "B1",
            "time": pd.Timestamp("2019-12-01") + pd.Timedelta(hours=i * 24),
            "lon": 60.0 + 0.2 * i,
            "lat": -68.0 + 0.05 * i,
            "source": "synthetic"
        })
    df = pd.DataFrame(rows)

    res = evaluate_iceberg_models(df, horizons_h=(24.0, 48.0))

    assert "constant_velocity_baseline" in res
    assert "physics_drift_model" in res
    assert res["is_synthetic"] is True
    assert 24 in res["physics_drift_model"]
    assert res["physics_drift_model"][24]["mean_km"] >= 0.0
