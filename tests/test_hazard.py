"""Unit tests for Phase 10 Polar Hazard Field (FR-15, FR-16, FR-17)."""

import numpy as np
import pytest

from backend.environment import EnvironmentState
from backend.hazard import (
    HazardComponentBreakdown,
    PolarHazardField,
    compute_iceberg_hazard,
    compute_ocean_hazard,
    compute_sea_ice_hazard,
    compute_weather_hazard,
)


def test_sea_ice_hazard_soft_and_hard_constraints():
    # Soft constraint (SIC 0.40 <= limit 0.80)
    h_soft, blocked_soft, _ = compute_sea_ice_hazard(0.40, max_sic_limit=0.80)
    assert 0.0 < h_soft < 0.50
    assert not blocked_soft

    # Hard constraint (SIC 0.85 > limit 0.80)
    h_hard, blocked_hard, reason = compute_sea_ice_hazard(0.85, max_sic_limit=0.80)
    assert h_hard == 1.0
    assert blocked_hard
    assert "exceeds vessel ice capability" in reason


def test_iceberg_hazard_gaussian_buffer():
    icebergs = [{"lon": 60.0, "lat": -68.0, "uncertainty_km": 1.0}]

    # At exact iceberg position -> max hazard 1.0
    h_center = compute_iceberg_hazard(60.0, -68.0, icebergs)
    assert h_center == pytest.approx(1.0)

    # 10 km away -> moderate hazard
    h_near = compute_iceberg_hazard(60.15, -68.0, icebergs)
    assert 0.0 < h_near < 1.0

    # 100 km away -> near zero hazard
    h_far = compute_iceberg_hazard(62.0, -68.0, icebergs)
    assert h_far < 0.01


def test_weather_hazard_limits():
    # Normal wind/wave -> soft risk
    h_norm, blocked_norm, _ = compute_weather_hazard(u10=5.0, v10=5.0, swh=1.5, max_swh_limit=4.0)
    assert 0.0 <= h_norm < 1.0
    assert not blocked_norm

    # Excessive wave height > limit -> blocked
    h_blocked, blocked_wave, reason = compute_weather_hazard(u10=5.0, v10=5.0, swh=5.0, max_swh_limit=4.0)
    assert h_blocked == 1.0
    assert blocked_wave
    assert "wave height" in reason


def test_vessel_specific_hazard_differentiation_fr17():
    state = EnvironmentState(
        timestamp="2019-12-05T00:00:00",
        lon=70.0,
        lat=-68.0,
        sic=0.40,  # 40% ice
        ice_mask=True,
        edge_dist_km=0.0,
        u10_m_s=8.0,
        v10_m_s=4.0,
        wind_speed_knots=17.4,
        wind_direction_deg=240.0,
        beaufort_scale=5,
        t2m_celsius=-2.0,
        mslp_hpa=1005.0,
        swh_m=2.0,
        uo_m_s=0.1,
        vo_m_s=0.05,
        current_speed_knots=0.22,
        ocean_source="glorys12",
        weather_severity=0.25,
        ocean_severity=0.15,
        overall_environment_risk=0.30,
    )

    hazard_model = PolarHazardField()

    # Open Water vessel (limit 0.15 SIC) -> BLOCKED
    bd_ow = hazard_model.evaluate_point_hazard(state, vessel_limits={"max_sic_limit": 0.15})
    assert bd_ow.is_blocked
    assert bd_ow.total_hazard == 1.0

    # PC1 Icebreaker (limit 1.00 SIC) -> NAVIGABLE (soft hazard)
    bd_pc1 = hazard_model.evaluate_point_hazard(state, vessel_limits={"max_sic_limit": 1.00})
    assert not bd_pc1.is_blocked
    assert bd_pc1.total_hazard < 1.0
    assert bd_pc1.total_hazard != bd_ow.total_hazard  # FR-17 differentiation


def test_decomposed_hazard_component_breakdown():
    state = EnvironmentState(
        timestamp="2019-12-05T00:00:00",
        lon=70.0,
        lat=-68.0,
        sic=0.20,
        ice_mask=True,
        edge_dist_km=0.0,
        u10_m_s=5.0,
        v10_m_s=5.0,
        wind_speed_knots=13.7,
        wind_direction_deg=225.0,
        beaufort_scale=4,
        t2m_celsius=0.0,
        mslp_hpa=1013.0,
        swh_m=1.0,
        uo_m_s=0.1,
        vo_m_s=0.1,
        current_speed_knots=0.27,
        ocean_source="glorys12",
        weather_severity=0.20,
        ocean_severity=0.15,
        overall_environment_risk=0.20,
    )

    hazard_model = PolarHazardField()
    bd = hazard_model.evaluate_point_hazard(state, vessel_limits={"max_sic_limit": 0.80})

    d = bd.to_dict()
    assert "total_hazard" in d
    assert "ice_hazard" in d
    assert "iceberg_hazard" in d
    assert "weather_hazard" in d
    assert "ocean_hazard" in d
    assert "is_blocked" in d
