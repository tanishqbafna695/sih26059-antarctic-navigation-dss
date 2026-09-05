"""Shared evaluation metrics for the Phase 5 baselines.

All metrics ignore NaN (missing/outside-coverage cells) so per-product missing
rates do not masquerade as skill.
"""
from __future__ import annotations

import numpy as np


def mae(truth: np.ndarray, forecast: np.ndarray) -> float:
    """Mean absolute error over cells where both truth and forecast are valid."""
    t = np.asarray(truth, dtype=float)
    f = np.asarray(forecast, dtype=float)
    valid = np.isfinite(t) & np.isfinite(f)
    if not valid.any():
        return float("nan")
    return float(np.mean(np.abs(t[valid] - f[valid])))


def rmse(truth: np.ndarray, forecast: np.ndarray) -> float:
    """Root mean squared error over cells where both are valid."""
    t = np.asarray(truth, dtype=float)
    f = np.asarray(forecast, dtype=float)
    valid = np.isfinite(t) & np.isfinite(f)
    if not valid.any():
        return float("nan")
    return float(np.sqrt(np.mean((t[valid] - f[valid]) ** 2)))


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in km between two lon/lat points."""
    r_earth = 6371.0
    p1, p2 = np.deg2rad(lat1), np.deg2rad(lat2)
    dp, dl = np.deg2rad(lat2 - lat1), np.deg2rad(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return float(2 * r_earth * np.arcsin(np.sqrt(a)))


def position_error_km(obs_lon: float, obs_lat: float,
                      pred_lon: float, pred_lat: float) -> float:
    """Distance between observed and predicted iceberg position (km)."""
    return haversine_km(obs_lon, obs_lat, pred_lon, pred_lat)
