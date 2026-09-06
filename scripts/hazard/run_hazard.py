"""CLI runner to evaluate Polar Hazard Field H(x, t, v) across vessel profiles and export JSON report.

Saves report to data/hazard/latest.json.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.environment import EnvironmentStore
from backend.hazard import PolarHazardField


def main() -> None:
    print("=== SIH26059 Phase 10 — Polar Hazard Field Evaluation ===")

    processed_nc = REPO_ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"
    if not processed_nc.exists():
        print(f"Processed feature store missing at {processed_nc}. Building synthetic scenario store...")
        from backend.data_pipeline.config import get_scenario, load_config
        from backend.data_pipeline.features import build_feature_store
        from backend.data_pipeline.synthetic import make_synthetic_products

        cfg = load_config()
        scen = get_scenario(cfg, "bharati_maitri_2019_20")
        out_dir = REPO_ROOT / "data"
        make_synthetic_products(scen, out_dir)
        build_feature_store(out_dir / "raw", processed_nc)

    print(f"Loading environment store from: {processed_nc}")
    store = EnvironmentStore.from_file(processed_nc)

    hazard_model = PolarHazardField()

    vessel_profiles = [
        {"name": "Open Water Research Vessel", "max_sic_limit": 0.15, "max_swh_limit": 2.5, "max_wind_limit": 25.0},
        {"name": "Polar Class PC7 Vessel", "max_sic_limit": 0.60, "max_swh_limit": 4.0, "max_wind_limit": 34.0},
        {"name": "Heavy Icebreaker PC1", "max_sic_limit": 1.00, "max_swh_limit": 6.0, "max_wind_limit": 50.0},
    ]

    # Sample icebergs
    sample_icebergs = [
        {"lon": 70.0, "lat": -68.0, "uncertainty_km": 2.0},
        {"lon": 45.0, "lat": -67.5, "uncertainty_km": 4.0},
    ]

    t_sample = "2019-12-05T00:00:00"

    vessel_results = []
    print(f"\n--- VESSEL-SPECIFIC HAZARD COMPARISON ({t_sample}) ---")

    for v_prof in vessel_profiles:
        limits = {
            "max_sic_limit": v_prof["max_sic_limit"],
            "max_swh_limit": v_prof["max_swh_limit"],
            "max_wind_limit": v_prof["max_wind_limit"],
        }

        # Point evaluation at ice-edge location (68.0S, 70.0E)
        st = store.get_state(70.0, -68.0, t_sample)
        breakdown = hazard_model.evaluate_point_hazard(st, icebergs=sample_icebergs, vessel_limits=limits)

        # Grid evaluation
        grid_res = hazard_model.compute_hazard_grid(store, time=t_sample, vessel_limits=limits)
        navigable_fraction = float(np.mean(grid_res["navigable_mask"]))
        mean_hazard = float(np.mean(grid_res["total_hazard"]))

        v_entry = {
            "vessel_name": v_prof["name"],
            "max_sic_limit": v_prof["max_sic_limit"],
            "point_breakdown_at_pydz_bay": breakdown.to_dict(),
            "grid_navigable_fraction": round(navigable_fraction, 4),
            "grid_mean_hazard": round(mean_hazard, 4),
        }
        vessel_results.append(v_entry)

        print(f"[{v_prof['name']}] (SIC Limit: {v_prof['max_sic_limit'] * 100:.0f}%)")
        print(f"  Prydz Bay Hazard: {breakdown.total_hazard:.2f} (Blocked: {breakdown.is_blocked})")
        print(f"  Domain Navigable Area: {navigable_fraction * 100:.1f}% | Domain Mean Hazard: {mean_hazard:.2f}")

    report = {
        "scenario": "bharati_maitri_2019_20",
        "sampled_timestamp": t_sample,
        "vessel_evaluations": vessel_results,
    }

    out_dir = REPO_ROOT / "data" / "hazard"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved hazard field evaluation report to: {out_path}")


if __name__ == "__main__":
    main()
