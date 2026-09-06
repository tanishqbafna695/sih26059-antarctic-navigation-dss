"""NFR-3 timing verification: full SC-1 demo story in < 2 minutes.

Runs the complete operator workflow programmatically through the API:
  1. Load feature store
  2. Select vessel (PC7)
  3. Plan routes (fastest/safest/balanced)
  4. Generate recommendation
  5. Generate explanation
  6. Switch vessel (PC1) — different answer
  7. Switch vessel (OW) — no route
  8. Re-route with new iceberg
  9. Generate change explanation

Measures wall-clock time for each step and the total. Asserts total < 120s.

Usage:
    python scripts/demo/verify_timing.py
    python scripts/demo/verify_timing.py --json  # machine-readable output
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import xarray as xr
from backend.explanation import explain_recommendation
from backend.rerouting.reroute import RerouteThresholds, reroute
from backend.routing.optimizer import NoRouteFound, plan_routes
from backend.tradeoff.comparison import build_comparison
from backend.tradeoff.recommend import recommend
from backend.vessel.profile import VesselRegistry

STORE = ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"
ORIGIN = (-69.41, 76.19)
DEST = (-70.77, 11.73)
NFR3_LIMIT_S = 120.0


def run_demo_story() -> dict:
    """Execute the full SC-1 operator workflow and return timing data."""
    reg = VesselRegistry()
    steps = []
    total_start = time.time()

    def timed(name, fn):
        t0 = time.time()
        result = fn()
        elapsed = round(time.time() - t0, 3)
        steps.append({"name": name, "elapsed_s": elapsed, "status": "ok"})
        return result

    # Step 1: Load feature store
    def _load():
        return xr.open_dataset(str(STORE), engine="h5netcdf")
    ds = timed("load_feature_store", _load)

    # Step 2: Plan routes (PC7)
    pc7 = reg.get_profile("polar_class_pc7")
    def _plan_pc7():
        return plan_routes(ds, ORIGIN, DEST, pc7, depart_day_index=45, icebergs=[])
    plan = timed("plan_routes_pc7", _plan_pc7)

    # Step 3: Build comparison
    comp = timed("build_comparison", lambda: build_comparison(plan))

    # Step 4: Recommend (balanced)
    rec = timed("recommend_balanced", lambda: recommend(comp, "balanced"))

    # Step 5: Explain
    vessel_info = {"name": pc7.name, "ice_class": pc7.ice_class,
                   "max_sic_limit": float(pc7.max_sic_limit)}
    expl = timed("explain_recommendation",
                 lambda: explain_recommendation(comp["rows"], rec, vessel_info))

    # Step 6: Switch to PC1
    pc1 = reg.get_profile("polar_class_pc1")
    def _plan_pc1():
        return plan_routes(ds, ORIGIN, DEST, pc1, depart_day_index=45, icebergs=[])
    plan_pc1 = timed("plan_routes_pc1", _plan_pc1)
    comp_pc1 = timed("compare_pc1", lambda: build_comparison(plan_pc1))
    rec_pc1 = timed("recommend_pc1", lambda: recommend(comp_pc1, "balanced"))

    # Step 7: Switch to OW (no-route)
    ow = reg.get_profile("open_water_rv")
    def _plan_ow():
        try:
            plan_routes(ds, ORIGIN, DEST, ow, depart_day_index=45, icebergs=[])
            return {"no_route": False}
        except NoRouteFound as e:
            return {"no_route": True, "reason": str(e)}
    ow_result = timed("plan_routes_ow_no_route", _plan_ow)

    # Step 8: Re-route with iceberg
    old_path = plan["routes"]["safest"]["path_xy"]
    import numpy as np
    lat2d = np.asarray(ds["lat"].values)
    lon2d = np.asarray(ds["lon"].values)
    mid = len(old_path) // 2
    mid_lat = float(lat2d[old_path[mid][0], old_path[mid][1]])
    mid_lon = float(lon2d[old_path[mid][0], old_path[mid][1]])
    new_bergs = [{"lon": mid_lon, "lat": mid_lat,
                  "v_east_kmh": 0, "v_north_kmh": 0,
                  "obs_staleness_h": 0, "label": "ASSUMED SC-5"}]
    def _reroute():
        return reroute(ds, pc7, [tuple(p) for p in old_path], "safest",
                       45, [], elapsed_h=120.0, new_depart_day=50,
                       new_icebergs=new_bergs,
                       thresholds=RerouteThresholds(min_hazard_delta=0.005))
    rer = timed("reroute_sc5", _reroute)

    total_elapsed = round(time.time() - total_start, 3)

    return {
        "total_elapsed_s": total_elapsed,
        "nfr3_limit_s": NFR3_LIMIT_S,
        "nfr3_pass": total_elapsed < NFR3_LIMIT_S,
        "steps": steps,
        "results": {
            "pc7_recommendation": rec["recommended"],
            "pc1_recommendation": rec_pc1["recommended"],
            "ow_no_route": ow_result["no_route"],
            "reroute_outcome": rer["outcome"],
            "explanation_headline": expl["headline"][:80],
        },
    }


def main():
    ap = argparse.ArgumentParser(description="NFR-3 timing verification")
    ap.add_argument("--json", action="store_true", help="Machine-readable output")
    args = ap.parse_args()

    result = run_demo_story()

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 60)
        print("  NFR-3 Timing Verification")
        print("=" * 60)
        for s in result["steps"]:
            print(f"  {s['name']:30s}  {s['elapsed_s']:.3f}s  [{s['status']}]")
        print("-" * 60)
        print(f"  {'TOTAL':30s}  {result['total_elapsed_s']:.3f}s")
        print(f"  NFR-3 limit: {result['nfr3_limit_s']:.0f}s")
        print(f"  NFR-3 PASS:  {result['nfr3_pass']}")
        print()
        r = result["results"]
        print(f"  PC7 recommendation: {r['pc7_recommendation']}")
        print(f"  PC1 recommendation: {r['pc1_recommendation']}")
        print(f"  OW no-route:       {r['ow_no_route']}")
        print(f"  Reroute outcome:   {r['reroute_outcome']}")
        print(f"  Explanation:       {r['explanation_headline']}")
        print()

    sys.exit(0 if result["nfr3_pass"] else 1)


if __name__ == "__main__":
    main()
