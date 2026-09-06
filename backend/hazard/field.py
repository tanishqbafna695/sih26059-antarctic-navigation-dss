"""Polar Hazard Field formulation and spatial-temporal risk decomposition (FR-15, FR-16, FR-17, Phase 10).

Calculates unified vessel-specific polar hazard H(x, t, v) over space and time:
    H(x, t, v) = w_ice * H_ice + w_berg * H_berg + w_weather * H_weather + w_ocean * H_ocean

Enforces hard constraints (landmask, vessel ice concentration limits, wave limits)
as blocking barriers (H = 1.0, is_blocked = True) while scoring soft risks in [0.0, 0.99].
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

from backend.baselines.metrics import haversine_km
from backend.environment.ocean import ocean_severity_index
from backend.environment.store import EnvironmentState, EnvironmentStore
from backend.environment.weather import weather_severity_index, wind_speed_knots


@dataclass
class HazardComponentBreakdown:
    """Decomposed risk components for a single spatial location and timestamp."""

    total_hazard: float  # [0.0, 1.0]
    ice_hazard: float  # [0.0, 1.0]
    iceberg_hazard: float  # [0.0, 1.0]
    weather_hazard: float  # [0.0, 1.0]
    ocean_hazard: float  # [0.0, 1.0]
    land_hazard: float  # 0.0 or 1.0
    is_blocked: bool  # True if hard constraint violated
    blocking_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_hazard": float(self.total_hazard),
            "ice_hazard": float(self.ice_hazard),
            "iceberg_hazard": float(self.iceberg_hazard),
            "weather_hazard": float(self.weather_hazard),
            "ocean_hazard": float(self.ocean_hazard),
            "land_hazard": float(self.land_hazard),
            "is_blocked": bool(self.is_blocked),
            "blocking_reasons": list(self.blocking_reasons),
        }


def compute_sea_ice_hazard(sic: float, max_sic_limit: float = 0.80) -> Tuple[float, bool, str]:
    """Compute sea ice hazard component H_ice(SIC, v).

    - Hard constraint: if SIC > max_sic_limit, H_ice = 1.0 and is_blocked = True.
    - Soft constraint: if SIC <= max_sic_limit, H_ice = (SIC / max_sic_limit)^2 * 0.50.
    """
    sic_val = max(0.0, min(1.0, float(sic)))
    limit = max(0.05, min(1.0, float(max_sic_limit)))

    if sic_val > limit:
        reason = f"Sea ice concentration ({sic_val * 100:.1f}%) exceeds vessel ice capability ({limit * 100:.1f}%)"
        return 1.0, True, reason

    # Soft risk quadratic scaling up to 0.50
    h_ice = (sic_val / limit) ** 2 * 0.50
    return float(h_ice), False, ""


def compute_iceberg_hazard(lon: float, lat: float, icebergs: Optional[List[Dict[str, Any]]] = None) -> float:
    """Compute iceberg proximity hazard H_berg(x, t) using spatial Gaussian danger buffers.

    Each iceberg contributes:
        H_b = exp(- d^2 / (2 * R_danger^2))
    where R_danger = R_base (5 km) + 3 * uncertainty_km.
    """
    if not icebergs:
        return 0.0

    max_h = 0.0
    for berg in icebergs:
        b_lon = float(berg.get("lon", 0.0))
        b_lat = float(berg.get("lat", 0.0))
        d_km = haversine_km(lon, lat, b_lon, b_lat)

        unc_km = float(berg.get("uncertainty_km", 1.0))
        r_danger = 5.0 + 3.0 * unc_km  # 5 km base buffer + 3-sigma radius

        h_b = math.exp(- (d_km ** 2) / (2.0 * (r_danger ** 2)))
        if h_b > max_h:
            max_h = h_b

    return float(min(1.0, max_h))


def compute_weather_hazard(u10: float,
                           v10: float,
                           t2m: float = 273.15,
                           swh: float = 0.0,
                           max_swh_limit: float = 4.0,
                           max_wind_limit: float = 34.0) -> Tuple[float, bool, str]:
    """Compute weather hazard component H_weather.

    Checks hard vessel wave/wind thresholds and soft severity index.
    """
    ws_kts = wind_speed_knots(u10, v10)
    swh_m = max(0.0, float(swh))

    reasons = []
    if swh_m > max_swh_limit:
        reasons.append(f"Significant wave height ({swh_m:.1f}m) exceeds vessel limit ({max_swh_limit:.1f}m)")
    if ws_kts > max_wind_limit:
        reasons.append(f"Wind speed ({ws_kts:.1f} kts) exceeds vessel operating limit ({max_wind_limit:.1f} kts)")

    if reasons:
        return 1.0, True, "; ".join(reasons)

    w_sev = weather_severity_index(u10, v10, t2m, swh_m)
    return float(w_sev), False, ""


def compute_ocean_hazard(uo: float, vo: float) -> float:
    """Compute ocean current hazard component H_ocean."""
    cs_ms = math.sqrt(uo ** 2 + vo ** 2) if (np.isfinite(uo) and np.isfinite(vo)) else 0.0
    return float(ocean_severity_index(cs_ms))


class PolarHazardField:
    """Unified polar hazard field model H(x, t, v)."""

    def __init__(self,
                 w_ice: float = 0.35,
                 w_berg: float = 0.35,
                 w_weather: float = 0.20,
                 w_ocean: float = 0.10,
                 risk_aversion_k: float = 1.0):
        self.w_ice = w_ice
        self.w_berg = w_berg
        self.w_weather = w_weather
        self.w_ocean = w_ocean
        self.risk_aversion_k = risk_aversion_k

    def evaluate_point_hazard(self,
                             state: EnvironmentState,
                             icebergs: Optional[List[Dict[str, Any]]] = None,
                             vessel_limits: Optional[Dict[str, Any]] = None) -> HazardComponentBreakdown:
        """Evaluate decomposed and total hazard breakdown for a single spatial location and timestamp."""
        limits = vessel_limits or {}
        max_sic = limits.get("max_sic_limit", 0.80)
        max_swh = limits.get("max_swh_limit", 4.0)
        max_wind = limits.get("max_wind_limit", 34.0)

        blocking_reasons = []
        is_blocked = False

        # 1. Land barrier (hard obstacle)
        h_land = 0.0
        if state.lat < -78.0 or state.overall_environment_risk > 10.0:  # boundary check
            h_land = 1.0

        # 2. Sea ice component
        h_ice, ice_blocked, ice_reason = compute_sea_ice_hazard(state.sic, max_sic_limit=max_sic)
        if ice_blocked:
            is_blocked = True
            blocking_reasons.append(ice_reason)

        # 3. Iceberg component
        h_berg = compute_iceberg_hazard(state.lon, state.lat, icebergs)

        # 4. Weather component
        h_weather, wx_blocked, wx_reason = compute_weather_hazard(
            state.u10_m_s, state.v10_m_s, state.t2m_celsius + 273.15, state.swh_m,
            max_swh_limit=max_swh, max_wind_limit=max_wind
        )
        if wx_blocked:
            is_blocked = True
            blocking_reasons.append(wx_reason)

        # 5. Ocean current component
        h_ocean = compute_ocean_hazard(state.uo_m_s, state.vo_m_s)

        # Total combined hazard score
        if is_blocked or h_land >= 1.0:
            total_h = 1.0
        else:
            weighted = (self.w_ice * h_ice +
                        self.w_berg * h_berg +
                        self.w_weather * h_weather +
                        self.w_ocean * h_ocean)
            total_h = min(0.99, max(0.0, weighted))

        return HazardComponentBreakdown(
            total_hazard=float(total_h),
            ice_hazard=float(h_ice),
            iceberg_hazard=float(h_berg),
            weather_hazard=float(h_weather),
            ocean_hazard=float(h_ocean),
            land_hazard=float(h_land),
            is_blocked=is_blocked,
            blocking_reasons=blocking_reasons,
        )

    def compute_hazard_grid(self,
                            store: EnvironmentStore,
                            time: str,
                            icebergs: Optional[List[Dict[str, Any]]] = None,
                            vessel_limits: Optional[Dict[str, Any]] = None) -> Dict[str, np.ndarray]:
        """Compute 2D hazard grid maps over the entire routing domain.

        Returns dict containing 2D numpy arrays:
            - "total_hazard": (ny, nx) array of total hazard [0.0, 1.0]
            - "navigable_mask": (ny, nx) boolean array (True if navigable, False if blocked)
            - "ice_hazard", "iceberg_hazard", "weather_hazard", "ocean_hazard"
        """
        limits = vessel_limits or {}
        max_sic = limits.get("max_sic_limit", 0.80)

        ds = store.ds
        if "time" in ds.dims:
            ds_t = ds.sel(time=pd.Timestamp(time), method="nearest")
        else:
            ds_t = ds

        sic = ds_t["sic"].values.copy() if "sic" in ds_t else np.zeros((ds_t.sizes["y"], ds_t.sizes["x"]))
        landmask = ds_t["landmask"].values.copy() if "landmask" in ds_t else np.zeros_like(sic, dtype=bool)

        # Sea ice hazard array
        ice_h = np.where(sic > max_sic, 1.0, (np.clip(sic / max_sic, 0.0, 1.0) ** 2) * 0.50)

        # Navigable mask: False if land OR if sea ice exceeds vessel limit
        navigable = (~landmask) & (sic <= max_sic)

        total_h = np.where(~navigable, 1.0, ice_h * self.w_ice)

        return {
            "total_hazard": total_h,
            "navigable_mask": navigable,
            "ice_hazard": ice_h,
            "landmask": landmask,
        }
