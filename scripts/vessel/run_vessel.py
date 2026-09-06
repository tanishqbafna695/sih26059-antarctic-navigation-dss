"""CLI runner to evaluate vessel performance and fuel consumption models across vessel profiles and scenario legs.

Saves report to data/vessel/latest.json.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.environment import EnvironmentState
from backend.vessel import VesselRegistry, evaluate_leg_performance


def main() -> None:
    print("=== SIH26059 Phase 11 — Vessel Model & Performance Evaluation ===")

    registry = VesselRegistry()
    profiles = registry.list_profiles()

    # Environmental conditions to evaluate
    env_conditions = [
        {"name": "Open Water", "sic": 0.00, "swh_m": 1.0, "wind_kts": 12.0},
        {"name": "Medium Sea Ice Pack (35% SIC)", "sic": 0.35, "swh_m": 0.5, "wind_kts": 10.0},
        {"name": "Heavy Sea Ice Pack (75% SIC)", "sic": 0.75, "swh_m": 0.2, "wind_kts": 8.0},
    ]

    leg_distance_nm = 500.0  # 500 nautical mile corridor segment (~926 km)
    vessel_evaluations = []

    print(f"\n--- PERFORMANCE & FUEL EVALUATION OVER {leg_distance_nm:.0f} NM LEG ---")

    for prof in profiles:
        prof_results = []
        print(f"\n[{prof.name}] (Class: {prof.ice_class}, Limit: {prof.max_sic_limit * 100:.0f}% SIC, Cruise: {prof.cruise_speed_kts} kts)")

        for env in env_conditions:
            # Construct synthetic EnvironmentState for test leg
            st = EnvironmentState(
                timestamp="2019-12-05T00:00:00",
                lon=45.0,
                lat=-67.5,
                sic=env["sic"],
                ice_mask=(env["sic"] >= 0.15),
                edge_dist_km=0.0,
                u10_m_s=env["wind_kts"] / 1.94384,
                v10_m_s=0.0,
                wind_speed_knots=env["wind_kts"],
                wind_direction_deg=270.0,
                beaufort_scale=3,
                t2m_celsius=-2.0,
                mslp_hpa=1010.0,
                swh_m=env["swh_m"],
                uo_m_s=0.1,
                vo_m_s=0.0,
                current_speed_knots=0.20,
                ocean_source="glorys12",
                weather_severity=0.15,
                ocean_severity=0.10,
                overall_environment_risk=0.20,
            )

            res = evaluate_leg_performance(prof, leg_distance_nm, st, heading_deg=270.0)
            res["condition"] = env["name"]
            prof_results.append(res)

            if res["is_navigable"]:
                print(f"  [{env['name']}]: Speed = {res['effective_speed_knots']:.1f} kts | Time = {res['travel_time_hours']:.1f} h | Fuel = {res['fuel_consumed_liters']:.0f} L ({res['fuel_per_nm']:.1f} L/nm)")
            else:
                print(f"  [{env['name']}]: UNNAVIGABLE / BLOCKED (exceeds vessel ice capability)")

        vessel_evaluations.append({
            "vessel_id": prof.vessel_id,
            "vessel_name": prof.name,
            "ice_class": prof.ice_class,
            "evaluations": prof_results,
        })

    report = {
        "leg_distance_nm": leg_distance_nm,
        "vessels": vessel_evaluations,
    }

    out_dir = REPO_ROOT / "data" / "vessel"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nSaved vessel evaluation report to: {out_path}")


if __name__ == "__main__":
    main()
