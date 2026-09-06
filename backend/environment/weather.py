"""Atmospheric weather processing and severity indexing (FR-8, Phase 8).

Computes derived weather variables (wind speed, direction, Beaufort scale,
wave severity, and combined weather risk index) from ERA5 atmospheric forcing.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Union

import numpy as np


def wind_speed_m_s(u10: Union[float, np.ndarray], v10: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Compute 10m wind speed in m/s from horizontal components."""
    return np.sqrt(np.asarray(u10) ** 2 + np.asarray(v10) ** 2)


def wind_speed_knots(u10: Union[float, np.ndarray], v10: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Compute 10m wind speed in knots (1 m/s = 1.94384 knots)."""
    return wind_speed_m_s(u10, v10) * 1.94384


def wind_direction_deg(u10: float, v10: float) -> float:
    """Compute meteorological wind direction in degrees (direction FROM which wind blows, 0-360)."""
    # math.atan2(u, v) gives direction TO which wind blows in rad from North
    dir_to_rad = math.atan2(u10, v10)
    dir_from_deg = (math.degrees(dir_to_rad) + 180.0) % 360.0
    return float(dir_from_deg)


def beaufort_scale(wind_speed_kts: float) -> int:
    """Map wind speed in knots to Beaufort wind force scale (0 to 12)."""
    ws = max(0.0, float(wind_speed_kts))
    if ws < 1.0:
        return 0
    elif ws < 4.0:
        return 1
    elif ws < 7.0:
        return 2
    elif ws < 11.0:
        return 3
    elif ws < 17.0:
        return 4
    elif ws < 22.0:
        return 5
    elif ws < 28.0:
        return 6
    elif ws < 34.0:
        return 7
    elif ws < 41.0:
        return 8
    elif ws < 48.0:
        return 9
    elif ws < 56.0:
        return 10
    elif ws < 64.0:
        return 11
    else:
        return 12


def wave_severity_index(swh_m: float) -> float:
    """Compute normalized wave severity index in [0.0, 1.0] from significant wave height (meters).

    - 0.0 - 1.25m (Calm to Slight): low severity (0.0 - 0.2)
    - 1.25m - 2.5m (Moderate): moderate severity (0.2 - 0.4)
    - 2.5m - 4.0m (Rough): high severity (0.4 - 0.7)
    - > 4.0m (Very Rough to High): critical severity (0.7 - 1.0)
    """
    h = max(0.0, float(swh_m))
    if h <= 1.25:
        return float(0.2 * (h / 1.25))
    elif h <= 2.5:
        return float(0.2 + 0.2 * ((h - 1.25) / 1.25))
    elif h <= 4.0:
        return float(0.4 + 0.3 * ((h - 2.5) / 1.5))
    else:
        return float(min(1.0, 0.7 + 0.3 * ((h - 4.0) / 4.0)))


def weather_severity_index(u10: float,
                           v10: float,
                           t2m_k: float = 273.15,
                           swh_m: float = 0.0) -> float:
    """Compute overall combined weather risk severity score in [0.0, 1.0].

    Combines:
        - Wind severity (Beaufort scale / 12)
        - Wave severity (wave_severity_index)
        - Temperature severity (freezing spray risk below -5 deg C)
    """
    ws_kts = wind_speed_knots(u10, v10)
    bft = beaufort_scale(ws_kts)
    wind_sev = float(bft / 12.0)

    wave_sev = wave_severity_index(swh_m)

    # Air temperature risk (freezing spray risk below 268.15 K / -5 C)
    t_celsius = t2m_k - 273.15
    if t_celsius < -15.0:
        temp_sev = 0.8
    elif t_celsius < -5.0:
        temp_sev = 0.4
    else:
        temp_sev = 0.0

    # Combined weighted severity (wind 50%, wave 35%, temp 15%)
    combined = 0.50 * wind_sev + 0.35 * wave_sev + 0.15 * temp_sev
    return float(min(1.0, max(0.0, combined)))


def analyze_weather(u10: float,
                    v10: float,
                    t2m_k: float = 273.15,
                    mslp_pa: float = 101325.0,
                    swh_m: float = 0.0,
                    mwp_s: float = 0.0) -> Dict[str, Any]:
    """Analyze atmospheric weather conditions and return structured summary dict."""
    ws_ms = wind_speed_m_s(u10, v10)
    ws_kts = wind_speed_knots(u10, v10)
    wdir = wind_direction_deg(u10, v10)
    bft = beaufort_scale(ws_kts)
    sev = weather_severity_index(u10, v10, t2m_k, swh_m)

    t_celsius = t2m_k - 273.15
    mslp_hpa = mslp_pa / 100.0 if mslp_pa > 2000.0 else mslp_pa

    return {
        "wind_speed_ms": float(ws_ms),
        "wind_speed_knots": float(ws_kts),
        "wind_direction_deg": float(wdir),
        "beaufort_scale": bft,
        "temperature_celsius": float(t_celsius),
        "pressure_hpa": float(mslp_hpa),
        "significant_wave_height_m": float(swh_m),
        "wave_period_s": float(mwp_s),
        "wave_severity": float(wave_severity_index(swh_m)),
        "weather_severity_index": float(sev),
    }
