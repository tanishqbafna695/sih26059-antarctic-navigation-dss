"""Unit tests for Phase 11 Vessel Model and Fuel Engine (FR-18, FR-19, FR-20)."""

import pytest

from backend.environment import EnvironmentState
from backend.vessel import (
    PRESET_PROFILES,
    VesselProfile,
    VesselRegistry,
    calculate_effective_speed,
    calculate_fuel_rate,
    evaluate_leg_performance,
)


def test_vessel_registry_lookup_and_custom_profile():
    reg = VesselRegistry()

    # Preset lookup
    p_ow = reg.get_profile("open_water_rv")
    assert p_ow.max_sic_limit == 0.15

    p_pc1 = reg.get_profile("polar_class_pc1")
    assert p_pc1.max_sic_limit == 1.00

    # Custom profile override (FR-19)
    custom = reg.create_custom_profile("polar_class_pc7", {"max_sic_limit": 0.70, "cruise_speed_kts": 13.0})
    assert custom.max_sic_limit == 0.70
    assert custom.cruise_speed_kts == 13.0
    assert custom.vessel_id == "polar_class_pc7_custom"


def test_speed_degradation_in_sea_ice():
    p_pc7 = PRESET_PROFILES["polar_class_pc7"]  # cruise = 12 kts, max_sic = 0.60

    # Open water -> cruise speed (12 kts)
    v_open = calculate_effective_speed(p_pc7, sic=0.0)
    assert v_open == pytest.approx(12.0)

    # 30% ice -> moderate speed drop
    v_ice30 = calculate_effective_speed(p_pc7, sic=0.30)
    assert 5.0 < v_ice30 < 12.0

    # 70% ice (> limit 0.60) -> 0.0 (blocked)
    v_blocked = calculate_effective_speed(p_pc7, sic=0.70)
    assert v_blocked == 0.0


def test_fuel_consumption_escalation_in_ice():
    p_pc1 = PRESET_PROFILES["polar_class_pc1"]  # base = 900 L/h, max = 1800 L/h, max_sic = 1.00

    # Open water cruising fuel rate
    f_open = calculate_fuel_rate(p_pc1, speed_kts=15.0, sic=0.0)
    assert f_open == pytest.approx(900.0)

    # 50% ice at 10 kts vs open water at 10 kts (368 L/h -> 525 L/h due to ice resistance)
    f_open_10 = calculate_fuel_rate(p_pc1, speed_kts=10.0, sic=0.0)
    f_ice_10 = calculate_fuel_rate(p_pc1, speed_kts=10.0, sic=0.50)
    assert f_ice_10 > f_open_10 * 1.30


def test_evaluate_leg_performance():
    p_pc7 = PRESET_PROFILES["polar_class_pc7"]

    st_open = EnvironmentState(
        timestamp="2019-12-05T00:00:00",
        lon=45.0,
        lat=-67.5,
        sic=0.0,
        ice_mask=False,
        edge_dist_km=10.0,
        u10_m_s=5.0,
        v10_m_s=0.0,
        wind_speed_knots=9.7,
        wind_direction_deg=270.0,
        beaufort_scale=3,
        t2m_celsius=0.0,
        mslp_hpa=1013.0,
        swh_m=1.0,
        uo_m_s=0.1,
        vo_m_s=0.0,
        current_speed_knots=0.20,
        ocean_source="glorys12",
        weather_severity=0.10,
        ocean_severity=0.10,
        overall_environment_risk=0.10,
    )

    leg_open = evaluate_leg_performance(p_pc7, dist_nm=120.0, state=st_open)
    assert leg_open["is_navigable"]
    assert leg_open["travel_time_hours"] == pytest.approx(10.0, rel=0.1)  # 120 nm @ ~12 kts = ~10 h
    assert leg_open["fuel_consumed_liters"] > 0.0

    # Unnavigable leg (exceeds ice class)
    st_heavy = EnvironmentState(
        timestamp="2019-12-05T00:00:00",
        lon=45.0,
        lat=-67.5,
        sic=0.85,  # 85% ice > PC7 limit (0.60)
        ice_mask=True,
        edge_dist_km=0.0,
        u10_m_s=5.0,
        v10_m_s=0.0,
        wind_speed_knots=9.7,
        wind_direction_deg=270.0,
        beaufort_scale=3,
        t2m_celsius=-5.0,
        mslp_hpa=1013.0,
        swh_m=0.5,
        uo_m_s=0.0,
        vo_m_s=0.0,
        current_speed_knots=0.0,
        ocean_source="glorys12",
        weather_severity=0.10,
        ocean_severity=0.10,
        overall_environment_risk=0.85,
    )

    leg_blocked = evaluate_leg_performance(p_pc7, dist_nm=120.0, state=st_heavy)
    assert not leg_blocked["is_navigable"]
    assert leg_blocked["travel_time_hours"] == float("inf")
