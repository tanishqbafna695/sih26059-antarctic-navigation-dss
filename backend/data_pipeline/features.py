"""Feature generation on the common grid (input store for Phases 6-12).

Output: one daily xarray Dataset at the common routing grid containing sea
ice (concentration, mask, edge distance), drift, atmospheric forcing, waves,
and ocean currents — the environment state consumed by hazard (Phase 10) and
routing (Phase 12).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import xarray as xr
from scipy.ndimage import distance_transform_edt

ICE_THRESHOLD = 0.15  # 15% concentration = ice-covered cell (matches common convention)


def ice_mask(sic: np.ndarray, landmask: np.ndarray | None = None) -> np.ndarray:
    mask = np.asarray(sic) >= ICE_THRESHOLD
    if landmask is not None:
        mask = mask & ~np.asarray(landmask, dtype=bool)
    return mask


def ice_edge_distance(ice: np.ndarray, spacing_km: float) -> np.ndarray:
    """km from each cell to the nearest ice-covered cell (0 inside the ice pack)."""
    ice = np.asarray(ice, dtype=bool)
    dist = distance_transform_edt(~ice) * spacing_km
    return np.where(ice, 0.0, dist)


def _load_processed(processed_dir: Path, name: str) -> xr.Dataset:
    path = processed_dir / f"{name}.nc"
    if not path.exists():
        raise FileNotFoundError(f"processed product missing: {path}")
    return xr.open_dataset(path, engine="h5netcdf")


def build_feature_store(processed_dir: Path, out_path: Path,
                        product_ids: list[str] | None = None,
                        drift_period_days: float = 2.0,
                        spacing_km: float | None = None) -> xr.Dataset:
    """Merge processed per-product datasets into one daily feature store."""
    ids = product_ids or ["sic", "drift", "era5", "glorys12"]
    datasets = {}
    for pid in ids:
        if (processed_dir / f"{pid}.nc").exists():
            datasets[pid] = _load_processed(processed_dir, pid)

    merged = xr.merge(list(datasets.values()), join="outer", compat="override")

    sic = merged["sic"].astype(float) / 100.0 if "sic" in merged else None
    if sic is None:
        raise ValueError("feature store requires a 'sic' product")
    sic = sic.clip(0.0, 1.0)  # regridding can overshoot by ~1e-17; SIC is a fraction

    landmask = None
    if "landmask" in merged.data_vars:
        landmask = merged["landmask"].astype(bool)
        sic = sic.where(~landmask)
    elif "landmask" in sic.attrs:
        landmask = np.asarray(sic.attrs["landmask"], dtype=bool)

    spacing = spacing_km or float(merged.attrs.get("spacing_km", 25.0))
    mask = ice_mask(sic.values, None if landmask is None else landmask.values)
    edge = ice_edge_distance(mask, spacing)

    store = merged
    store = store.assign(
        sic=sic,
        ice_mask=(("time", "y", "x"), mask),
        edge_dist=(("time", "y", "x"), edge),
    )
    if "drift_x" in store and "drift_y" in store:
        dt = drift_period_days * 86400.0
        store = store.assign(
            drift_u=store["drift_x"] / dt,
            drift_v=store["drift_y"] / dt,
        )
    if landmask is not None:
        store = store.assign(landmask=(("y", "x"), landmask.values))

    store.attrs["scenario"] = str(merged.attrs.get("scenario", ""))
    store.attrs["ice_threshold"] = ICE_THRESHOLD
    store.attrs["drift_period_days"] = drift_period_days

    out_path.parent.mkdir(parents=True, exist_ok=True)
    store.to_netcdf(out_path, engine="h5netcdf", invalid_netcdf=True)  # bool vars
    return store