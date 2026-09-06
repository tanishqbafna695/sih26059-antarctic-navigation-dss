"""Vectorized per-day cost fields for Phase 12 routing (FR-22, FR-23).

This module precomputes, for one dataset day, the 2-D grids the time-aware
search needs: vessel-specific total hazard, direction-independent base speed,
fuel reference quantities, and iceberg proximity hazard.

MATH (mirrors the scalar Phase 8/10/11 functions exactly; a consistency test
in tests/test_routing.py asserts vector == scalar on sample cells):

- wind speed (kts) = 1.94384 * sqrt(u10^2 + v10^2)      [environment.weather]
- Beaufort via np.digitize on the documented thresholds  [environment.weather]
- weather severity = 0.50*(bft/12) + 0.35*wave_sev(swh) + 0.15*temp_sev(t2m)
- ocean current fallback: GLORYS12 uo/vo -> sea-ice drift -> 2% wind with
  -20 deg leftward deflection                              [environment.ocean]
- ocean severity piecewise on current speed                [environment.ocean]
- sea-ice hazard: blocked if sic > limit else (sic/limit)^2 * 0.50
                                                              [hazard.field]
- iceberg hazard: max over bergs of exp(-d^2 / (2*R^2)), R = 5 + 3*unc_km
- weather hazard: blocked if swh/wind over vessel limits else weather severity
- total hazard: 1.0 if any hard block else
  min(0.99, w_ice*H_ice + w_berg*H_berg + w_wx*H_wx + w_oc*H_oc)
- base through-water speed = V_cruise * f_ice * f_weather, with
  f_ice = max(0.10, 1 - 0.70*(sic/limit)^2), f_weather = max(0.50, ...)
                                                              [vessel.performance]
  (the along-track current projection is direction-dependent, so it is added
  per edge in optimizer.py, not here)
- fuel rate = min(F_max, F_base*(V/V_cruise)^2.2 * ice_load * (1+0.02*bft))

Icebergs are advected from their base fix to the requested day with the
Phase 7 physics model in kinematic mode (has_forcing=False, ASSUMED: no
forcing coupling in the MVP router; forcing-coupled advection is a Phase 15
refinement). Uncertainty grows with horizon inside that model.

Weight presets (FR-22; configurable by the caller):
- fastest:  time-dominated   (a=0.05, b=1.0, g=0.05)
- safest:   risk-dominated   (a=1.0, b=0.05, g=0.05)
- balanced: explicit trade-off (a=0.5, b=0.5, g=0.30)
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np
import xarray as xr

WEIGHT_PRESETS: Dict[str, Dict[str, float]] = {
    "fastest": {"alpha": 0.05, "beta": 1.00, "gamma": 0.05},
    "safest": {"alpha": 1.00, "beta": 0.05, "gamma": 0.05},
    "balanced": {"alpha": 0.50, "beta": 0.50, "gamma": 0.30},
}

_BFT_EDGES = np.array([1.0, 4.0, 7.0, 11.0, 17.0, 22.0, 28.0, 34.0, 41.0, 48.0, 56.0, 64.0])
_KTS_PER_MS = 1.94384
_KM_PER_NM = 1.852


def beaufort_grid(wind_kts: np.ndarray) -> np.ndarray:
    """Vectorized Beaufort scale matching environment.weather.beaufort_scale."""
    return np.digitize(np.maximum(0.0, np.asarray(wind_kts, dtype=float)), _BFT_EDGES)


def wave_severity_grid(swh_m: np.ndarray) -> np.ndarray:
    """Vectorized wave severity matching environment.weather.wave_severity_index."""
    h = np.maximum(0.0, np.asarray(swh_m, dtype=float))
    out = np.empty_like(h)
    m1 = h <= 1.25
    m2 = (h > 1.25) & (h <= 2.5)
    m3 = (h > 2.5) & (h <= 4.0)
    m4 = h > 4.0
    out[m1] = 0.2 * (h[m1] / 1.25)
    out[m2] = 0.2 + 0.2 * ((h[m2] - 1.25) / 1.25)
    out[m3] = 0.4 + 0.3 * ((h[m3] - 2.5) / 1.5)
    out[m4] = np.minimum(1.0, 0.7 + 0.3 * ((h[m4] - 4.0) / 4.0))
    return out


def weather_severity_grid(u10: np.ndarray, v10: np.ndarray,
                          t2m_k: np.ndarray, swh_m: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized weather severity; returns (severity, wind_kts, beaufort)."""
    u10 = np.asarray(u10, dtype=float)
    v10 = np.asarray(v10, dtype=float)
    ws_kts = np.sqrt(u10 ** 2 + v10 ** 2) * _KTS_PER_MS
    bft = beaufort_grid(ws_kts)
    wind_sev = bft / 12.0
    wave_sev = wave_severity_grid(swh_m)
    t_c = np.asarray(t2m_k, dtype=float) - 273.15
    temp_sev = np.where(t_c < -15.0, 0.8, np.where(t_c < -5.0, 0.4, 0.0))
    sev = np.minimum(1.0, np.maximum(0.0, 0.50 * wind_sev + 0.35 * wave_sev + 0.15 * temp_sev))
    return sev, ws_kts, bft


def ocean_current_grids(uo: Optional[np.ndarray], vo: Optional[np.ndarray],
                        u10: np.ndarray, v10: np.ndarray,
                        drift_u: Optional[np.ndarray] = None,
                        drift_v: Optional[np.ndarray] = None) -> tuple[np.ndarray, np.ndarray, str]:
    """Vectorized 3-tier ocean fallback matching environment.ocean (GLORYS12 ->
    sea-ice drift -> wind-driven estimate). Returns (uo, vo, source)."""
    u10a = np.asarray(u10, dtype=float)
    v10a = np.asarray(v10, dtype=float)
    shape = u10a.shape

    def _arr(v):
        if v is None:
            return np.full(shape, np.nan)
        a = np.asarray(v, dtype=float)
        return np.broadcast_to(a, shape).copy()

    uo_a, vo_a = _arr(uo), _arr(vo)
    du_a, dv_a = _arr(drift_u), _arr(drift_v)
    ok_ocean = np.isfinite(uo_a) & np.isfinite(vo_a)
    ok_drift = np.isfinite(du_a) & np.isfinite(dv_a)

    rad = math.radians(-20.0)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    u_rot = cos_a * np.nan_to_num(u10a) - sin_a * np.nan_to_num(v10a)
    v_rot = sin_a * np.nan_to_num(u10a) + cos_a * np.nan_to_num(v10a)
    uo_wind, vo_wind = 0.02 * u_rot, 0.02 * v_rot

    uo_out = np.where(ok_ocean, uo_a, np.where(ok_drift, du_a, uo_wind))
    vo_out = np.where(ok_ocean, vo_a, np.where(ok_drift, dv_a, vo_wind))
    if bool(np.all(ok_ocean)):
        source = "glorys12"
    elif bool(np.all(ok_drift | ok_ocean)):
        source = "mixed_glorys12_drift"
    else:
        source = "wind_driven_estimate"
    return uo_out, vo_out, source


def ocean_severity_grid(cs_ms: np.ndarray) -> np.ndarray:
    """Vectorized ocean severity matching environment.ocean.ocean_severity_index."""
    cs = np.maximum(0.0, np.asarray(cs_ms, dtype=float))
    out = np.empty_like(cs)
    m1 = cs <= 0.25
    m2 = (cs > 0.25) & (cs <= 0.75)
    m3 = cs > 0.75
    out[m1] = 0.2 * (cs[m1] / 0.25)
    out[m2] = 0.2 + 0.3 * ((cs[m2] - 0.25) / 0.50)
    out[m3] = np.minimum(1.0, 0.5 + 0.5 * ((cs[m3] - 0.75) / 0.75))
    return out


def advect_icebergs_to_day(icebergs: List[Dict[str, Any]], day_offset_h: float) -> List[Dict[str, Any]]:
    """Advect iceberg base fixes forward by day_offset_h hours (kinematic mode).

    Each input berg needs lon/lat (+ optional v_east_kmh/v_north_kmh and
    obs_staleness_h). Returns bergs with predicted lon/lat/uncertainty_km.
    """
    if not icebergs or day_offset_h <= 0:
        return [dict(b) for b in (icebergs or [])]
    from backend.iceberg.drift import IcebergPhysicsDriftModel
    model = IcebergPhysicsDriftModel()
    out = []
    for b in icebergs:
        pred = model.predict_position(
            float(b["lon"]), float(b["lat"]),
            float(b.get("v_east_kmh", 0.0)), float(b.get("v_north_kmh", 0.0)),
            float(day_offset_h),
            obs_staleness_h=float(b.get("obs_staleness_h", 0.0)),
            has_forcing=False,
        )
        nb = dict(b)
        nb["lon"], nb["lat"], nb["uncertainty_km"] = pred["lon"], pred["lat"], pred["uncertainty_km"]
        out.append(nb)
    return out


def iceberg_hazard_grid(lon2d: np.ndarray, lat2d: np.ndarray,
                        icebergs: Optional[List[Dict[str, Any]]]) -> np.ndarray:
    """Vectorized Gaussian iceberg proximity hazard (matches hazard.field)."""
    from backend.baselines.metrics import haversine_km  # scalar; loop over bergs only
    shape = np.asarray(lon2d).shape
    if not icebergs:
        return np.zeros(shape)
    # vectorized haversine per berg over the 2-D grid
    lon = np.asarray(lon2d, dtype=float)
    lat = np.asarray(lat2d, dtype=float)
    r_earth = 6371.0
    p_lat = np.deg2rad(lat)
    best = np.zeros(shape)
    for b in icebergs:
        p2 = math.radians(float(b["lat"]))
        dp = np.radians(float(b["lat"]) - lat)
        dl = np.radians(float(b["lon"]) - lon)
        a = np.sin(dp / 2.0) ** 2 + np.cos(p_lat) * math.cos(p2) * np.sin(dl / 2.0) ** 2
        d = 2.0 * r_earth * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))
        r_danger = 5.0 + 3.0 * float(b.get("uncertainty_km", 1.0))
        h_b = np.exp(-(d ** 2) / (2.0 * r_danger ** 2))
        np.maximum(best, h_b, out=best)
    return np.minimum(1.0, best)


def _day_var(ds_day: xr.Dataset, name: str, default: float) -> np.ndarray:
    if name in ds_day:
        v = np.asarray(ds_day[name].values, dtype=float)
        return v
    shape = (int(ds_day.sizes["y"]), int(ds_day.sizes["x"]))
    return np.full(shape, default)


def build_day_fields(ds: xr.Dataset, day_index: int, profile,
                     hazard_weights: Optional[Dict[str, float]] = None,
                     icebergs: Optional[List[Dict[str, Any]]] = None,
                     depart_day_index: int = 0) -> Dict[str, Any]:
    """Build all 2-D routing fields for one dataset day.

    profile: VesselProfile (limits + speeds + fuel). hazard_weights: dict with
    w_ice/w_berg/w_weather/w_ocean (defaults 0.35/0.35/0.20/0.10, Phase 10).
    depart_day_index anchors iceberg advection (bergs forecast forward from it).
    """
    w = {"w_ice": 0.35, "w_berg": 0.35, "w_weather": 0.20, "w_ocean": 0.10}
    if hazard_weights:
        w.update(hazard_weights)
    n_days = int(ds.sizes["time"])
    day_index = int(max(0, min(n_days - 1, day_index)))
    ds_day = ds.isel(time=day_index)

    sic = np.clip(_day_var(ds_day, "sic", np.nan), 0.0, 1.0)
    valid = np.isfinite(sic)
    # Forcing imputation (mirrors EnvironmentStore._val defaults): ERA5/GLORYS
    # regridding leaves NaN outside each product's native box even where SIC is
    # valid. Impossible values are replaced by documented neutral defaults and
    # the imputed fraction is reported (honesty: never silent; the ocean part
    # is additionally flagged via missing_inputs in optimizer.plan_routes).
    u10_raw = _day_var(ds_day, "u10", 0.0)
    forcing_imputed_frac = float(np.mean(~np.isfinite(u10_raw[valid]))) if valid.any() else 0.0
    u10 = np.nan_to_num(u10_raw, nan=0.0)
    v10 = np.nan_to_num(_day_var(ds_day, "v10", 0.0), nan=0.0)
    t2m = np.nan_to_num(_day_var(ds_day, "t2m", 273.15), nan=273.15)
    swh = np.nan_to_num(_day_var(ds_day, "swh", 0.0), nan=0.0)
    uo_raw = ds_day["uo"].values if "uo" in ds_day else None
    vo_raw = ds_day["vo"].values if "vo" in ds_day else None
    du_raw = ds_day["drift_u"].values if "drift_u" in ds_day else None
    dv_raw = ds_day["drift_v"].values if "drift_v" in ds_day else None

    sic_lim = max(0.05, min(1.0, float(profile.max_sic_limit)))
    w_sev, ws_kts, bft = weather_severity_grid(u10, v10, t2m, swh)
    uo, vo, ocean_source = ocean_current_grids(uo_raw, vo_raw, u10, v10, du_raw, dv_raw)
    cs_ms = np.sqrt(uo ** 2 + vo ** 2)
    o_sev = ocean_severity_grid(cs_ms)

    # --- hazard components (vector mirrors of hazard.field) ---
    ice_blocked = valid & (sic > sic_lim)
    h_ice = np.where(valid, (np.clip(sic / sic_lim, 0.0, 1.0) ** 2) * 0.50, 0.0)

    lon2d = np.asarray(ds_day["lon"].values if "lon" in ds_day.coords or "lon" in ds_day else ds["lon"].values)
    lat2d = np.asarray(ds_day["lat"].values if "lat" in ds_day.coords or "lat" in ds_day else ds["lat"].values)
    day_offset_h = max(0.0, (day_index - depart_day_index) * 24.0)
    bergs_now = advect_icebergs_to_day(icebergs, day_offset_h)
    h_berg = iceberg_hazard_grid(lon2d, lat2d, bergs_now)

    wx_blocked = (swh > float(profile.max_swh_limit)) | (ws_kts > float(profile.max_wind_limit))
    h_wx = w_sev
    h_oc = o_sev

    blocked = (~valid) | ice_blocked | wx_blocked
    weighted = w["w_ice"] * h_ice + w["w_berg"] * h_berg + w["w_weather"] * h_wx + w["w_ocean"] * h_oc
    h_total = np.where(blocked, 1.0, np.minimum(0.99, np.maximum(0.0, weighted)))

    # --- vessel speed/fuel direction-independent parts ---
    v_cruise = float(profile.cruise_speed_kts)
    f_ice = np.where(sic > 0.0, np.maximum(0.10, 1.0 - 0.70 * ((np.clip(sic, 0, 1) / sic_lim) ** 2)), 1.0)
    f_ice = np.where(valid, f_ice, 0.0)
    wind_pen = 0.015 * np.maximum(0.0, ws_kts - 15.0)
    wave_pen = 0.04 * np.maximum(0.0, swh)
    f_wx = np.maximum(0.50, 1.0 - wind_pen - wave_pen)
    base_speed = v_cruise * f_ice * f_wx  # through-water; current added per edge
    base_speed = np.where(valid & (~ice_blocked), base_speed, 0.0)

    return {
        "day_index": day_index,
        "sic": sic,
        "valid": valid,
        "blocked": blocked,
        "ice_blocked": ice_blocked,
        "wx_blocked": wx_blocked,
        "hazard_total": h_total,
        "ice_hazard": np.where(valid, h_ice, 0.0),
        "berg_hazard": h_berg,
        "weather_hazard": h_wx,
        "ocean_hazard": h_oc,
        "wind_kts": ws_kts,
        "beaufort": bft,
        "swh": swh,
        "uo": uo,
        "vo": vo,
        "ocean_source": ocean_source,
        "base_speed_kts": base_speed,
        "lon2d": lon2d,
        "lat2d": lat2d,
        "icebergs_today": bergs_now,
        "forcing_imputed_frac": forcing_imputed_frac,
    }


class DayFieldsCache:
    """Lazy per-day field cache over the dataset time axis (FR-23).

    max_day_index (optional, Phase 16 SC-4): freeze observations — days past
    the cap return the cap day's fields, modeling a SIMULATED sensor outage
    where the system persists its last observation (labeled by the caller).
    """

    def __init__(self, ds: xr.Dataset, profile,
                 hazard_weights: Optional[Dict[str, float]] = None,
                 icebergs: Optional[List[Dict[str, Any]]] = None,
                 depart_day_index: int = 0,
                 max_day_index: Optional[int] = None):
        self.ds = ds
        self.profile = profile
        self.hazard_weights = hazard_weights
        self.icebergs = icebergs or []
        self.depart_day_index = depart_day_index
        self.max_day_index = max_day_index
        self._cache: Dict[int, Dict[str, Any]] = {}
        self.n_days = int(ds.sizes["time"])

    def day(self, elapsed_h: float) -> Dict[str, Any]:
        idx = self.depart_day_index + int(max(0.0, elapsed_h) // 24)
        idx = max(0, min(self.n_days - 1, idx))
        if self.max_day_index is not None:
            idx = min(idx, self.max_day_index)
        if idx not in self._cache:
            self._cache[idx] = build_day_fields(
                self.ds, idx, self.profile, self.hazard_weights,
                self.icebergs, self.depart_day_index)
        return self._cache[idx]

    @property
    def days_built(self) -> List[int]:
        return sorted(self._cache)
