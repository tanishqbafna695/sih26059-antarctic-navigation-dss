"""Evaluation harness for iceberg trajectory prediction models (FR-8, FR-9, FR-10).

Evaluates physics-guided and ML iceberg trajectory models against the Phase 5
Constant-Velocity baseline on iceberg track datasets.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from backend.baselines.iceberg import _estimate_velocity as estimate_cv_velocity, constant_velocity_predict
from backend.baselines.metrics import position_error_km
from .drift import IcebergPhysicsDriftModel, _estimate_kinematic_velocity


def evaluate_iceberg_models(tracks: pd.DataFrame,
                             horizons_h: Tuple[float, ...] = (24.0, 48.0, 72.0),
                             forcing_provider: Optional[Any] = None) -> Dict[str, Any]:
    """Evaluate Physics Drift Model, ML Model, and Constant Velocity baseline on tracks.

    Returns dict containing per-horizon position error metrics (mean, median, max, n)
    for each model, along with uncertainty metrics and source transparency flags.
    """
    model_phys = IcebergPhysicsDriftModel()

    res_cv: Dict[int, list] = {int(h): [] for h in horizons_h}
    res_phys: Dict[int, list] = {int(h): [] for h in horizons_h}

    # Data source labeling check (FR-10)
    sources = tracks["source"].unique().tolist() if "source" in tracks.columns else ["unknown"]

    for _, berg in tracks.groupby("berg_id", sort=False):
        berg = berg.sort_values("time").reset_index(drop=True)
        if len(berg) < 2:
            continue

        times = pd.to_datetime(berg["time"])
        for i in range(len(berg) - 1):
            track_sub = berg.iloc[: i + 2]
            vlon_cv, vlat_cv, lon0, lat0 = estimate_cv_velocity(track_sub)
            v_kin_east, v_kin_north, _, _, _ = _estimate_kinematic_velocity(track_sub)

            t_base = times.iloc[i + 1]

            forcing = {}
            if forcing_provider is not None:
                forcing = forcing_provider(lon0, lat0, t_base)

            for h in horizons_h:
                target_t = t_base + pd.Timedelta(hours=h)
                match = berg[times == target_t]
                if len(match) == 0:
                    continue

                obs = match.iloc[0]
                obs_lon, obs_lat = float(obs["lon"]), float(obs["lat"])

                # 1. Constant Velocity baseline prediction
                pred_cv_lon, pred_cv_lat = constant_velocity_predict(lon0, lat0, vlon_cv, vlat_cv, h)
                err_cv = position_error_km(obs_lon, obs_lat, pred_cv_lon, pred_cv_lat)
                res_cv[int(h)].append(err_cv)

                # 2. Physics-guided drift model prediction
                u_wind = forcing.get("u10", 0.0)
                v_wind = forcing.get("v10", 0.0)
                u_ocean = forcing.get("uo", 0.0)
                v_ocean = forcing.get("vo", 0.0)

                pred_phys = model_phys.predict_position(
                    lon0, lat0, v_kin_east, v_kin_north, h,
                    u_wind_m_s=u_wind, v_wind_m_s=v_wind,
                    u_ocean_m_s=u_ocean, v_ocean_m_s=v_ocean,
                    has_forcing=(forcing_provider is not None)
                )
                err_phys = position_error_km(obs_lon, obs_lat, pred_phys["lon"], pred_phys["lat"])
                res_phys[int(h)].append({
                    "error_km": err_phys,
                    "uncertainty_km": pred_phys["uncertainty_km"],
                    "confidence": pred_phys["confidence"],
                })

    out: Dict[str, Any] = {
        "sources": sources,
        "is_synthetic": any("synthetic" in s.lower() for s in sources),
        "constant_velocity_baseline": {},
        "physics_drift_model": {},
    }

    for h in horizons_h:
        h_int = int(h)
        # CV baseline stats
        cv_errs = res_cv[h_int]
        if cv_errs:
            out["constant_velocity_baseline"][h_int] = {
                "mean_km": float(np.mean(cv_errs)),
                "median_km": float(np.median(cv_errs)),
                "max_km": float(np.max(cv_errs)),
                "n": len(cv_errs),
            }

        # Physics drift model stats
        phys_records = res_phys[h_int]
        if phys_records:
            p_errs = [r["error_km"] for r in phys_records]
            p_unc = [r["uncertainty_km"] for r in phys_records]
            p_conf = [r["confidence"] for r in phys_records]
            out["physics_drift_model"][h_int] = {
                "mean_km": float(np.mean(p_errs)),
                "median_km": float(np.median(p_errs)),
                "max_km": float(np.max(p_errs)),
                "mean_uncertainty_km": float(np.mean(p_unc)),
                "mean_confidence": float(np.mean(p_conf)),
                "n": len(p_errs),
            }

    return out
