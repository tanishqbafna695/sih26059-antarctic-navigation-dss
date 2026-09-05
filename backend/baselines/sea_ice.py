"""Persistence baseline for sea-ice concentration (FR-6).

The persistence forecast is: the SIC observed today is the SIC forecast for
all future horizons. Any ML/statistical SIC forecast must beat this on
MAE/RMSE at 1-5 day horizons before we claim skill (Phase 0 §6).

Inputs are 3-D (time, y, x) SIC fractions on the common grid. NaNs (missing
data / outside-coverage cells) are ignored by the metrics.
"""
from __future__ import annotations

import numpy as np


def persistence_forecast(sic: np.ndarray, horizon_days: int) -> np.ndarray:
    """Forecast sic[t+h] = sic[t]; return the array of valid (truth, forecast) pairs.

    For an array of T daily steps this produces T - h pairs: truth at times
    h..T-1 and the persistence forecast (the field h days earlier).
    """
    sic = np.asarray(sic, dtype=float)
    t = sic.shape[0]
    if horizon_days <= 0 or horizon_days >= t:
        raise ValueError(
            f"horizon {horizon_days} invalid for {t} timesteps; need 1 <= h < T")
    truth = sic[horizon_days:]
    forecast = sic[:-horizon_days]
    return truth, forecast


def evaluate_persistence(sic: np.ndarray, horizons: tuple[int, ...] = (1, 2, 3, 4, 5)) -> dict:
    """Evaluate persistence at each horizon; return {horizon: {mae, rmse}}."""
    from .metrics import mae, rmse  # local import: metrics has no heavy deps

    sic = np.asarray(sic, dtype=float)
    out: dict = {}
    for h in horizons:
        if h >= sic.shape[0]:
            continue
        truth, forecast = persistence_forecast(sic, h)
        out[int(h)] = {
            "mae": mae(truth, forecast),
            "rmse": rmse(truth, forecast),
            "n_pairs": int(sic.shape[0] - h),
        }
    return out
