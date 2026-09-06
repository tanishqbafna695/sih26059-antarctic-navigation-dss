"""Vessel Performance Model and Fuel Consumption Engine (FR-20, Phase 11).

Calculates effective vessel speed over ground V_eff (knots), travel time (hours),
and fuel consumption rate F_rate (Liters/hour) under sea ice, weather forcing,
and ocean current conditions.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np

from backend.environment.store import EnvironmentState
from backend.environment.weather import wind_speed_knots
from .profile import VesselProfile


def calculate_effective_speed(profile: VesselProfile,
                              sic: float,
                              wind_speed_kts: float = 0.0,
                              swh_m: float = 0.0,
                              current_along_track_kts: float = 0.0) -> float:
    """Compute effective vessel speed over ground V_eff in knots (FR-20).

    Formula:
        V_eff = max(0.5, V_cruise * f_ice * f_weather + V_current_along_track)
    """
    sic_val = max(0.0, min(1.0, float(sic)))
    ws_kts = max(0.0, float(wind_speed_kts))
    swh = max(0.0, float(swh_m))
    v_cruise = profile.cruise_speed_kts
    sic_lim = max(0.05, profile.max_sic_limit)

    # 1. Speed reduction in sea ice pack
    if sic_val > sic_lim:
        return 0.0  # Vessel blocked / cannot penetrate

    if sic_val > 0.0:
        # Quadratic speed penalty: in 50% ice, speed drops ~25%; in 80% ice, speed drops ~70%
        f_ice = max(0.10, 1.0 - 0.70 * ((sic_val / sic_lim) ** 2))
    else:
        f_ice = 1.0

    # 2. Speed reduction from adverse wind & waves
    wind_penalty = 0.015 * max(0.0, ws_kts - 15.0)
    wave_penalty = 0.04 * swh
    f_weather = max(0.50, 1.0 - wind_penalty - wave_penalty)

    # 3. Water speed through water
    v_water = v_cruise * f_ice * f_weather

    # 4. Ground speed incorporating along-track current
    v_eff = v_water + float(current_along_track_kts)
    return float(max(0.50, v_eff))


def calculate_fuel_rate(profile: VesselProfile,
                       speed_kts: float,
                       sic: float,
                       beaufort_scale: int = 0) -> float:
    """Compute fuel consumption rate F_rate in Liters/hour (FR-20).

    Formula:
        F_rate = min(F_max, F_base * (V / V_cruise)^2.5 * (1 + beta_ice * (SIC/SIC_limit)^1.5) * (1 + 0.02 * BFT))
    """
    sp_kts = max(0.10, float(speed_kts))
    sic_val = max(0.0, min(1.0, float(sic)))
    v_cruise = profile.cruise_speed_kts
    sic_lim = max(0.05, profile.max_sic_limit)
    f_base = profile.base_fuel_rate_lph
    f_max = profile.max_fuel_rate_lph

    # Speed power exponent (~2.5 cubic resistance scaling)
    l_speed = (sp_kts / v_cruise) ** 2.2

    # Icebreaking engine load multiplier (up to 2.2x base load in heavy ice)
    if sic_val > 0.0 and sic_val <= sic_lim:
        l_ice = 1.0 + 1.20 * ((sic_val / sic_lim) ** 1.5)
    elif sic_val > sic_lim:
        l_ice = 2.20
    else:
        l_ice = 1.0

    # Weather sea state load multiplier
    l_wx = 1.0 + 0.02 * max(0, int(beaufort_scale))

    f_rate = f_base * l_speed * l_ice * l_wx
    return float(min(f_max, max(f_base * 0.20, f_rate)))


def evaluate_leg_performance(profile: VesselProfile,
                             dist_nm: float,
                             state: EnvironmentState,
                             heading_deg: float = 0.0) -> Dict[str, Any]:
    """Evaluate voyage leg performance (time, fuel, effective speed, economy) for a given distance and state.

    Parameters:
        profile: VesselProfile
        dist_nm: Leg distance in nautical miles (1 nm = 1.852 km)
        state: EnvironmentState
        heading_deg: Vessel voyage heading angle in degrees (0-360)

    Returns:
        Dict with keys:
            - dist_nm: distance in nautical miles
            - dist_km: distance in kilometers
            - travel_time_hours: leg travel time in hours
            - effective_speed_knots: actual ground speed in knots
            - fuel_rate_lph: fuel burn rate in Liters/hour
            - fuel_consumed_liters: total fuel consumed on leg in Liters
            - fuel_per_nm: fuel economy in Liters/nautical mile
            - is_navigable: True if leg speed > 0 and not blocked
    """
    d_nm = max(0.01, float(dist_nm))
    d_km = d_nm * 1.852

    # Calculate ocean current component along vessel heading
    uo_kts = state.uo_m_s * 1.94384
    vo_kts = state.vo_m_s * 1.94384

    h_rad = math.radians(heading_deg)
    # Unit vector along heading
    u_h, v_h = math.sin(h_rad), math.cos(h_rad)
    current_along_kts = uo_kts * u_h + vo_kts * v_h

    # Calculate effective speed
    v_eff = calculate_effective_speed(
        profile, state.sic, state.wind_speed_knots, state.swh_m, current_along_kts
    )

    if v_eff <= 0.50 or state.sic > profile.max_sic_limit:
        return {
            "dist_nm": float(d_nm),
            "dist_km": float(d_km),
            "travel_time_hours": float("inf"),
            "effective_speed_knots": 0.0,
            "fuel_rate_lph": 0.0,
            "fuel_consumed_liters": float("inf"),
            "fuel_per_nm": float("inf"),
            "is_navigable": False,
        }

    t_hours = d_nm / v_eff
    f_rate = calculate_fuel_rate(profile, v_eff, state.sic, state.beaufort_scale)
    fuel_total = f_rate * t_hours
    fuel_per_nm = fuel_total / d_nm

    return {
        "dist_nm": float(d_nm),
        "dist_km": float(d_km),
        "travel_time_hours": float(t_hours),
        "effective_speed_knots": float(v_eff),
        "fuel_rate_lph": float(f_rate),
        "fuel_consumed_liters": float(fuel_total),
        "fuel_per_nm": float(fuel_per_nm),
        "is_navigable": True,
    }
