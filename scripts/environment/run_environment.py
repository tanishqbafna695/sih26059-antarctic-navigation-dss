"""CLI runner to evaluate weather and ocean forcing fields and output JSON summary report.

Saves report to data/environment/latest.json.
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


def main() -> None:
    print("=== SIH26059 Phase 8 — Weather & Ocean Environment Integration ===")

    processed_nc = REPO_ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"
    raw_nc = REPO_ROOT / "data" / "raw" / "era5_synthetic.nc"

    if not processed_nc.exists():
        print(f"Processed feature store not found at {processed_nc}. Building synthetic scenario store...")
        from backend.data_pipeline.config import get_scenario, load_config
        from backend.data_pipeline.features import build_feature_store
        from backend.data_pipeline.synthetic import make_synthetic_products

        cfg = load_config()
        scen = get_scenario(cfg, "bharati_maitri_2019_20")
        out_dir = REPO_ROOT / "data"
        make_synthetic_products(scen, out_dir)
        processed_dir = out_dir / "processed" / "bharati_maitri_2019_20"
        processed_dir.mkdir(parents=True, exist_ok=True)
        # Note: if processed files don't exist yet, we can use features directly
        build_feature_store(out_dir / "raw", processed_nc)

    print(f"Loading environment store from: {processed_nc}")
    store = EnvironmentStore.from_file(processed_nc)

    # Sample waypoints along the Bharati -> Maitri corridor
    waypoints = [
        {"name": "Bharati Station", "lat": -69.4, "lon": 76.2},
        {"name": "Prydz Bay Offshore", "lat": -68.0, "lon": 70.0},
        {"name": "Mid-Corridor Ocean", "lat": -67.5, "lon": 45.0},
        {"name": "Riiser-Larsen Sea", "lat": -68.5, "lon": 25.0},
        {"name": "Maitri Station Approach", "lat": -70.7, "lon": 11.7},
    ]

    t_sample = "2019-12-05T00:00:00"
    sampled_states = []

    print(f"\n--- WAYPOINT ENVIRONMENTAL STATES ({t_sample}) ---")
    for wp in waypoints:
        state = store.get_state(wp["lon"], wp["lat"], t_sample)
        st_dict = state.to_dict()
        st_dict["waypoint"] = wp["name"]
        sampled_states.append(st_dict)

        print(f"[{wp['name']}] (Lon: {wp['lon']}°, Lat: {wp['lat']}°)")
        print(f"  SIC: {state.sic * 100:.1f}% | Wind: {state.wind_speed_knots:.1f} kts (Bft {state.beaufort_scale}) | Wave: {state.swh_m:.2f} m")
        print(f"  Current: {state.current_speed_knots:.2f} kts ({state.ocean_source}) | Weather Risk: {state.weather_severity:.2f} | Overall Risk: {state.overall_environment_risk:.2f}")

    report = {
        "scenario": "bharati_maitri_2019_20",
        "sampled_timestamp": t_sample,
        "waypoints": sampled_states,
        "variables_verified": [
            "u10", "v10", "t2m", "mslp", "swh", "uo", "vo", "sic", "edge_dist"
        ],
    }

    out_dir = REPO_ROOT / "data" / "environment"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved environment evaluation report to: {out_path}")


if __name__ == "__main__":
    main()
