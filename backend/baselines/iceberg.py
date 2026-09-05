"""Constant-velocity baseline for iceberg trajectory (FR-9).

The baseline predicts: the iceberg keeps its most recently observed velocity,
so forecast position at time t+h is last_position + velocity * h. Any learned
trajectory model must beat this on position error (km) at 24/48/72 h before
we claim skill.

Works on tracks with columns: berg_id, time (ISO or datetime), lon, lat.
Extra columns (length_m, source) are ignored. Synthetic tracks are labeled
by `source` and never presented as real ground truth (FR-10).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import position_error_km

EARTH_R_KM = 6371.0


def _dx_km_per_deg_lon(lat_deg: float) -> float:
    """km per degree of longitude at a given latitude (spherical approx)."""
    return (np.pi / 180.0) * EARTH_R_KM * np.cos(np.deg2rad(lat_deg))


def constant_velocity_predict(lon0: float, lat0: float,
                              v_lon_kmh: float, v_lat_kmh: float,
                              horizon_h: float) -> tuple[float, float]:
    """Extrapolate position (lon, lat) from (lon0, lat0) at constant velocity.

    Velocity components are in km/h toward east/north. Longitude step is
    converted via the local km-per-degree-longitude factor.
    """
    dlat = v_lat_kmh * horizon_h
    dlat_deg = dlat / ((np.pi / 180.0) * EARTH_R_KM)
    lat1 = lat0 + dlat_deg
    # integrate longitude using the mean latitude for better accuracy
    km_deg = _dx_km_per_deg_lon(0.5 * (lat0 + lat1))
    dlon = v_lon_kmh * horizon_h
    lon1 = lon0 + dlon / km_deg
    return float(lon1), float(lat1)


def _estimate_velocity(df: pd.DataFrame) -> tuple[float, float, float, float]:
    """Velocity (km/h, east & north) from the LAST two fixes of a berg track."""
    p0, p1 = df.iloc[-2], df.iloc[-1]
    t0 = pd.Timestamp(p0["time"])
    t1 = pd.Timestamp(p1["time"])
    dt_h = (t1 - t0).total_seconds() / 3600.0
    if dt_h <= 0:
        return 0.0, 0.0, float(p1["lon"]), float(p1["lat"])
    # distance east/north in km
    km_deg_lon = _dx_km_per_deg_lon(0.5 * (float(p0["lat"]) + float(p1["lat"])))
    de = (float(p1["lon"]) - float(p0["lon"])) * km_deg_lon
    dn = (float(p1["lat"]) - float(p0["lat"])) * (np.pi / 180.0) * EARTH_R_KM
    return de / dt_h, dn / dt_h, float(p1["lon"]), float(p1["lat"])


def evaluate_constant_velocity(tracks: pd.DataFrame,
                               horizons_h: tuple[float, ...] = (24.0, 48.0, 72.0)) -> dict:
    """Per-horizon position error (km) of the constant-velocity baseline.

    For each berg, each consecutive (t_i, t_{i+1}) pair is treated as a
    "nowcast": velocity is estimated from those two fixes and extrapolated to
    t_{i+1} + h. If the true track has an observation at that time, the
    prediction error is recorded.
    """
    out: dict = {int(h): {"mean_km": float("nan"), "errors_km": []} for h in horizons_h}
    for _, berg in tracks.groupby("berg_id", sort=False):
        berg = berg.sort_values("time").reset_index(drop=True)
        times = pd.to_datetime(berg["time"])
        for i in range(len(berg) - 1):
            vlon, vlat, lon0, lat0 = _estimate_velocity(berg.iloc[: i + 2])
            t_base = times.iloc[i + 1]
            for h in horizons_h:
                target = t_base + pd.Timedelta(hours=h)
                match = berg[times == target]
                if len(match) == 0:
                    continue
                obs = match.iloc[0]
                plon, plat = constant_velocity_predict(lon0, lat0, vlon, vlat, h)
                err = position_error_km(float(obs["lon"]), float(obs["lat"]), plon, plat)
                out[int(h)]["errors_km"].append(err)
    for h, d in out.items():
        if d["errors_km"]:
            d["mean_km"] = float(np.mean(d["errors_km"]))
            d["median_km"] = float(np.median(d["errors_km"]))
            d["max_km"] = float(np.max(d["errors_km"]))
            d["n"] = len(d["errors_km"])
        del d["errors_km"]
    return out
