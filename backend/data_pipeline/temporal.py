"""Temporal alignment: continuous UTC axes, daily resampling, gap detection."""
from __future__ import annotations

import pandas as pd
import xarray as xr


def daily_timestamps(start: str, end: str) -> pd.DatetimeIndex:
    """Inclusive daily UTC axis between start and end (ISO strings)."""
    return pd.date_range(start, end, freq="D")


def align_time_axis(ds: xr.Dataset, start: str, end: str, freq: str = "D",
                    time_dim: str = "time") -> xr.Dataset:
    """Reindex onto a continuous UTC axis; missing steps become NaN (QC will flag them)."""
    if time_dim not in ds.dims:
        return ds
    idx = pd.date_range(start, end, freq=freq)
    return ds.reindex({time_dim: idx})


def resample_daily(ds: xr.Dataset, time_dim: str = "time") -> xr.Dataset:
    """Resample sub-daily data to daily means. No-op if already daily."""
    if time_dim not in ds.dims:
        return ds
    return ds.resample({time_dim: "D"}).mean()


def gap_stats(ds: xr.Dataset, time_dim: str = "time") -> dict:
    """Report missing timesteps per variable (missing-data honesty rule)."""
    if time_dim not in ds.dims:
        return {}
    stats = {}
    for name, var in ds.data_vars.items():
        if time_dim not in var.dims:
            continue
        n_missing = int(var.isel(**{time_dim: 0}).isnull().sum().item())
        stats[name] = {"missing_steps": n_missing,
                       "missing_rate": float(var.isnull().mean().item())}
    return stats