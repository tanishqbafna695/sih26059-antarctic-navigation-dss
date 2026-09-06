"""Ocean current physics processing and fallback estimation (Phase 8).

Processes surface ocean currents (GLORYS12 uo, vo, SST) and provides empirical
surface drift fallback derived from atmospheric wind and sea-ice drift when
ocean netCDF data is missing or unmeasured.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Tuple, Union

import numpy as np


def current_speed_m_s(uo: Union[float, np.ndarray], vo: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Compute ocean surface current speed in m/s."""
    return np.sqrt(np.asarray(uo) ** 2 + np.asarray(vo) ** 2)


def current_speed_knots(uo: Union[float, np.ndarray], vo: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """Compute ocean surface current speed in knots (1 m/s = 1.94384 knots)."""
    return current_speed_m_s(uo, vo) * 1.94384


def current_heading_deg(uo: float, vo: float) -> float:
    """Compute ocean current flow heading angle in degrees (0-360 TOWARD which current flows)."""
    heading_rad = math.atan2(uo, vo)
    return float(math.degrees(heading_rad) % 360.0)


def estimate_wind_driven_surface_current(u10_m_s: float,
                                         v10_m_s: float,
                                         wind_factor: float = 0.02,
                                         deflection_deg: float = -20.0) -> Tuple[float, float]:
    """Estimate empirical wind-driven surface ocean current vector (uo, vo) in m/s.

    In the Southern Ocean, surface ocean currents are strongly wind-driven (~2% of 10m wind speed
    deflected ~20 deg leftward due to Coriolis effect).
    """
    rad = math.radians(deflection_deg)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    u_rot = cos_a * u10_m_s - sin_a * v10_m_s
    v_rot = sin_a * u10_m_s + cos_a * v10_m_s

    uo_est = wind_factor * u_rot
    vo_est = wind_factor * v_rot
    return float(uo_est), float(vo_est)


def ocean_current_fallback(uo: float | None,
                           vo: float | None,
                           u10_m_s: float = 0.0,
                           v10_m_s: float = 0.0,
                           drift_u: float | None = None,
                           drift_v: float | None = None) -> Tuple[float, float, str]:
    """Get valid surface ocean current vector (uo, vo) in m/s with documented fallback chain.

    Fallback hierarchy:
        1. GLORYS12 ocean current (if valid / non-NaN) -> source="glorys12"
        2. Sea-ice drift velocity (if valid / non-NaN) -> source="sea_ice_drift"
        3. Empirical wind-driven surface current -> source="wind_driven_estimate"
    """
    # 1. Check GLORYS12 ocean current
    if uo is not None and vo is not None and np.isfinite(uo) and np.isfinite(vo):
        return float(uo), float(vo), "glorys12"

    # 2. Check Sea-ice drift
    if drift_u is not None and drift_v is not None and np.isfinite(drift_u) and np.isfinite(drift_v):
        return float(drift_u), float(drift_v), "sea_ice_drift"

    # 3. Fallback to empirical wind-driven current estimate
    uo_est, vo_est = estimate_wind_driven_surface_current(u10_m_s, v10_m_s)
    return uo_est, vo_est, "wind_driven_estimate"


def ocean_severity_index(current_speed_m_s_val: float) -> float:
    """Compute normalized ocean current severity index in [0.0, 1.0].

    - 0.0 - 0.25 m/s (~0.5 kts): low impact (0.0 - 0.2)
    - 0.25 - 0.75 m/s (~1.5 kts): moderate impact (0.2 - 0.5)
    - > 0.75 m/s (> 1.5 kts): strong current impact (0.5 - 1.0)
    """
    cs = max(0.0, float(current_speed_m_s_val))
    if cs <= 0.25:
        return float(0.2 * (cs / 0.25))
    elif cs <= 0.75:
        return float(0.2 + 0.3 * ((cs - 0.25) / 0.50))
    else:
        return float(min(1.0, 0.5 + 0.5 * ((cs - 0.75) / 0.75)))


def analyze_ocean(uo: float | None,
                  vo: float | None,
                  u10_m_s: float = 0.0,
                  v10_m_s: float = 0.0,
                  drift_u: float | None = None,
                  drift_v: float | None = None,
                  sst_k: float = 271.15) -> Dict[str, Any]:
    """Analyze ocean current conditions and return structured summary dict."""
    uo_val, vo_val, source = ocean_current_fallback(uo, vo, u10_m_s, v10_m_s, drift_u, drift_v)

    cs_ms = current_speed_m_s(uo_val, vo_val)
    cs_kts = current_speed_knots(uo_val, vo_val)
    heading = current_heading_deg(uo_val, vo_val)
    sev = ocean_severity_index(cs_ms)

    sst_celsius = sst_k - 273.15 if sst_k > 100.0 else sst_k

    return {
        "uo_ms": float(uo_val),
        "vo_ms": float(vo_val),
        "current_speed_ms": float(cs_ms),
        "current_speed_knots": float(cs_kts),
        "current_heading_deg": float(heading),
        "sst_celsius": float(sst_celsius),
        "current_source": source,
        "ocean_severity_index": float(sev),
    }
