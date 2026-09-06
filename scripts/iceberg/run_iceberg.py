"""CLI script to run Phase 7 iceberg trajectory prediction evaluation and produce JSON benchmark report.

Saves report to data/iceberg/latest.json.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.iceberg import evaluate_iceberg_models


def main() -> None:
    print("=== SIH26059 Phase 7 — Iceberg Trajectory Prediction Evaluation ===")

    # Locate iceberg tracks file
    processed_csv = REPO_ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "icebergs.csv"
    raw_csv = REPO_ROOT / "data" / "raw" / "icebergs_synthetic.csv"

    if processed_csv.exists():
        track_path = processed_csv
    elif raw_csv.exists():
        track_path = raw_csv
    else:
        print("No processed or synthetic iceberg tracks found. Generating synthetic dataset...")
        from backend.data_pipeline.synthetic import make_synthetic_products
        from backend.data_pipeline.config import load_config, get_scenario
        cfg = load_config()
        scen = get_scenario(cfg, "bharati_maitri_2019_20")
        out_dir = REPO_ROOT / "data"
        paths = make_synthetic_products(scen, out_dir)
        track_path = Path(paths["icebergs"])

    print(f"Loading iceberg tracks from: {track_path}")
    tracks = pd.read_csv(track_path)
    print(f"Loaded {len(tracks)} track fixes for {tracks['berg_id'].nunique()} icebergs.")

    # Run model vs baseline evaluation
    report = evaluate_iceberg_models(tracks, horizons_h=(24.0, 48.0, 72.0))

    # Output directory
    out_dir = REPO_ROOT / "data" / "iceberg"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved benchmark evaluation report to: {out_path}")
    print("\n--- PERFORMANCE BENCHMARK RESULTS ---")
    cv_res = report.get("constant_velocity_baseline", {})
    phys_res = report.get("physics_drift_model", {})

    print(f"Data Sources: {report.get('sources')} (Synthetic: {report.get('is_synthetic')})")
    for h in [24, 48, 72]:
        cv_h = cv_res.get(h, cv_res.get(str(h), {}))
        phys_h = phys_res.get(h, phys_res.get(str(h), {}))
        cv_mean = cv_h.get("mean_km", float("nan"))
        phys_mean = phys_h.get("mean_km", float("nan"))
        phys_unc = phys_h.get("mean_uncertainty_km", float("nan"))
        print(f"  Horizon {h}h: CV Baseline = {cv_mean:.2f} km | Physics Drift Model = {phys_mean:.2f} km (Mean Unc: {phys_unc:.2f} km)")


if __name__ == "__main__":
    main()
