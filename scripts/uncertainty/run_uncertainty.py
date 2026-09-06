"""CLI runner to evaluate uncertainty engine metrics and output JSON summary report.

Saves report to data/uncertainty/latest.json.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.uncertainty import (
    UncertaintyEngine,
    compute_combined_confidence,
    compute_iceberg_uncertainty_ellipse,
    compute_sic_prediction_interval,
    uncertainty_aware_risk,
)


def main() -> None:
    print("=== SIH26059 Phase 9 — Uncertainty Engine Evaluation ===")

    engine = UncertaintyEngine(risk_aversion_k=1.5)

    # 1. Sea Ice Forecast Prediction Intervals across horizons
    sic_intervals = []
    for h_days in [1.0, 2.0, 3.0, 4.0, 5.0]:
        lower, upper, sigma = compute_sic_prediction_interval(0.50, horizon_days=h_days, confidence_level=0.90)
        sic_intervals.append({
            "horizon_days": h_days,
            "mean_sic": 0.50,
            "lower_90": round(lower, 4),
            "upper_90": round(upper, 4),
            "sigma_sic": round(sigma, 4),
        })

    # 2. Iceberg Trajectory Uncertainty Ellipses
    berg_ellipses = []
    for h_h in [24.0, 48.0, 72.0]:
        ell = compute_iceberg_uncertainty_ellipse(60.0, -68.0, 1.2, 0.5, horizon_h=h_h, obs_staleness_h=6.0)
        berg_ellipses.append(ell)

    # 3. Confidence Reports across operational scenarios
    scenarios_confidence = {
        "nominal_24h": compute_combined_confidence(horizon_h=24.0, staleness_h=0.0).to_dict(),
        "nominal_72h": compute_combined_confidence(horizon_h=72.0, staleness_h=0.0).to_dict(),
        "stale_obs_12h": compute_combined_confidence(horizon_h=24.0, staleness_h=12.0).to_dict(),
        "missing_satellite_sc4": compute_combined_confidence(horizon_h=24.0, staleness_h=24.0, missing_inputs=["sic_satellite"]).to_dict(),
    }

    # 4. Uncertainty-Aware Risk Modification (FR-14)
    risk_inflation_tests = []
    mean_risk = 0.40
    risk_std = 0.15
    for k in [0.0, 1.0, 2.0]:
        r_u = uncertainty_aware_risk(mean_risk, risk_std, risk_aversion_k=k)
        risk_inflation_tests.append({
            "risk_aversion_k": k,
            "mean_risk": mean_risk,
            "risk_std": risk_std,
            "uncertainty_aware_risk": round(r_u, 4),
        })

    report = {
        "sea_ice_prediction_intervals": sic_intervals,
        "iceberg_uncertainty_ellipses": berg_ellipses,
        "confidence_scenarios": scenarios_confidence,
        "risk_aversion_inflation_fr14": risk_inflation_tests,
    }

    out_dir = REPO_ROOT / "data" / "uncertainty"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n--- UNCERTAINTY BENCHMARK RESULTS ---")
    print("Sea-Ice 90% Intervals:")
    for item in sic_intervals:
        print(f"  h={item['horizon_days']}d: SIC [90% CI: {item['lower_90']:.3f} .. {item['upper_90']:.3f}] (sigma: {item['sigma_sic']:.3f})")

    print("\nIceberg Trajectory Ellipses:")
    for ell in berg_ellipses:
        print(f"  h={ell['horizon_h']}h: Radius = {ell['uncertainty_km']:.2f} km | Major = {ell['semi_major_km']:.2f} km | Minor = {ell['semi_minor_km']:.2f} km | Confidence = {ell['confidence']:.2f}")

    print("\nScenario Confidence Scores:")
    for sc_name, sc_data in scenarios_confidence.items():
        print(f"  [{sc_name}]: Confidence = {sc_data['overall_confidence']:.2f} ({sc_data['status_label']})")

    print(f"\nSaved uncertainty evaluation report to: {out_path}")


if __name__ == "__main__":
    main()
