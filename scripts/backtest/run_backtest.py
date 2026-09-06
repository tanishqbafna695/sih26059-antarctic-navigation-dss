"""CLI runner for Phase 16 backtesting (SC-1…SC-8 acceptance evidence).

- MATRIX (SC-1/2/6/7): full chain over vessel x depart-day pairs.
- SC-4: SIMULATED satellite outage (fields frozen at last observation +
  120 h staleness) vs fresh control on the same leg.
- SC-5 ice: mid-voyage update into the late-season refreeze (day 60->65).
- SC-8: pre-storm departure (day 70, transit crosses the day-73 corridor
  storm) vs calm day-55 baseline.
- SC-3: verifies the nowcast evidence files exist (built in Phases 8-10).
Writes data/backtest/latest.json.

Usage:
    python scripts/backtest/run_backtest.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import xarray as xr

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.backtest import run_departure_matrix, summarize_matrix  # noqa: E402
from backend.rerouting import RerouteThresholds, reroute  # noqa: E402
from backend.routing import NoRouteFound, plan_routes  # noqa: E402
from backend.vessel import VesselRegistry  # noqa: E402

DEFAULT_STORE = REPO_ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"
DEFAULT_ROUTING = REPO_ROOT / "data" / "routing" / "latest.json"
BHARATI = (-69.41, 76.19)
MAITRI = (-70.77, 11.73)


def _slim_routes(plan: dict) -> dict:
    return {n: {k: r[k] for k in ("travel_time_h", "fuel_liters",
                                  "mean_hazard", "max_hazard",
                                  "ice_exposure_frac", "n_cells")}
            for n, r in plan["routes"].items()}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Phase 16 backtesting")
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--routing", default=str(DEFAULT_ROUTING))
    ap.add_argument("--out", default=str(REPO_ROOT / "data" / "backtest"))
    args = ap.parse_args(argv)

    print("=== SIH26059 Phase 16 — Backtesting (SC-1..SC-8) ===")
    ds = xr.open_dataset(args.store, engine="h5netcdf")
    routing = json.loads(Path(args.routing).read_text(encoding="utf-8"))
    old_bergs = routing.get("icebergs_assumed", [])
    registry = VesselRegistry()
    report: dict = {"phase": 16}

    # ---- MATRIX (SC-1 primary legs, SC-2 planning pairs, SC-6/7) ----
    pairs = ([(v, d) for v in ("open_water_rv", "polar_class_pc7",
                               "polar_class_pc1") for d in (45, 55, 65)]
             + [("polar_class_pc7", 60)])
    matrix = run_departure_matrix(ds, pairs, old_bergs)
    summary = summarize_matrix(matrix)
    report["matrix"] = matrix
    report["matrix_summary"] = summary
    print(f"\n[MATRIX] {summary['n_success']}/{summary['n_cases']} routed "
          f"(rate {summary['success_rate']})")
    for key in matrix["pairs"]:
        e = matrix["entries"][key]
        print(f"  {key}: " + (f"{e['winner']} {e['time_h']:.0f}h risk {e['mean_hazard']:.3f}"
                              if e["found"] else f"NO ROUTE ({e['reason'][:60]})"))
    for d in summary["sc6_vessel_differences"]:
        print(f"  SC-6 day {d['depart_day']}: {d['outcomes']}")

    # ---- SC-4: simulated outage (frozen fields + staleness) ----
    pc7 = registry.get_profile("polar_class_pc7")
    vplan = routing["vessels"]["polar_class_pc7"]
    old_path = vplan["routes"]["safest"]["path_xy"]
    sc4 = reroute(ds, pc7, old_path, "safest", 45, old_bergs, 120.0, 50,
                  old_bergs, RerouteThresholds(), priority="balanced",
                  frozen_day_index=45, staleness_h=120.0,
                  extra_missing_inputs=["sic_satellite + iceberg feed "
                                        "(SIMULATED OUTAGE: last obs day 45)"])
    sc4_ctrl = reroute(ds, pc7, old_path, "safest", 45, old_bergs, 120.0, 50,
                       old_bergs, RerouteThresholds(), priority="balanced")
    report["sc4_simulated_outage"] = {
        "stale_confidence": sc4["confidence"],
        "fresh_confidence": sc4_ctrl["confidence"],
        "stale_outcome": sc4["outcome"],
        "note": "frozen day-45 fields model a sensor outage; confidence "
                "collapses via staleness + missing-input penalty (FR-3/12/13)",
    }
    print(f"\n[SC-4] stale confidence {sc4['confidence']['overall_confidence']:.2f} "
          f"({sc4['confidence']['status_label']}) vs fresh "
          f"{sc4_ctrl['confidence']['overall_confidence']:.2f} "
          f"({sc4_ctrl['confidence']['status_label']})")

    # ---- SC-5 ice: sail into the refreeze (day 60 -> 65) ----
    try:
        plan60 = plan_routes(ds, BHARATI, MAITRI, pc7, depart_day_index=60,
                             icebergs=old_bergs)
        w60 = plan60["routes"]["balanced"]
        sc5 = reroute(ds, pc7, w60["path_xy"], "balanced", 60, old_bergs,
                      120.0, 65, old_bergs, RerouteThresholds(),
                      priority="balanced")
        for r in sc5.get("new_routes", {}).values():
            r.pop("path_xy", None)
        report["sc5_ice_refreeze"] = {
            "day60_balanced": {k: w60[k] for k in ("travel_time_h", "fuel_liters",
                                                   "mean_hazard", "ice_exposure_frac")},
            "outcome": sc5["outcome"],
            "trigger": sc5["changes"]["trigger_text"],
            "stay_vs_new": {
                "stay": sc5["old_remaining_if_staying"],
                "new": sc5["new_routes"][sc5["new_recommendation"]["recommended"]]},
        }
        print(f"\n[SC-5] day-60 balanced risk {w60['mean_hazard']:.3f} -> "
              f"update outcome {sc5['outcome']} ({sc5['changes']['trigger_text']})")
    except NoRouteFound as e:
        report["sc5_ice_refreeze"] = {"outcome": "NO_ROUTE", "reason": str(e)}
        print(f"\n[SC-5] day-60 plan itself unroutable: {e}")

    # ---- SC-8: pre-storm departure vs calm ----
    sc8 = {}
    for label, day in (("calm_day55", 55), ("prestorm_day70", 70)):
        try:
            p = plan_routes(ds, BHARATI, MAITRI, pc7, depart_day_index=day,
                            icebergs=old_bergs)
            sc8[label] = {"found": True, "routes": _slim_routes(p),
                          "days_evaluated": p["days_evaluated"]}
        except NoRouteFound as e:
            sc8[label] = {"found": False, "reason": str(e)}
    report["sc8_storm"] = sc8
    for label, r in sc8.items():
        print(f"\n[SC-8] {label}: " + ("NO ROUTE" if not r["found"] else
              f"fastest {r['routes']['fastest']['travel_time_h']:.0f}h risk "
              f"{r['routes']['fastest']['mean_hazard']:.3f} max "
              f"{r['routes']['fastest']['max_hazard']:.3f}"))

    # ---- SC-3: nowcast evidence files ----
    sc3 = {f: (REPO_ROOT / "data" / f / "latest.json").exists()
           for f in ("environment", "hazard", "uncertainty", "baselines")}
    report["sc3_nowcast_files"] = sc3
    print(f"\n[SC-3] nowcast evidence present: {sc3}")

    ds.close()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved backtest report to: {out_path}")


if __name__ == "__main__":
    main()
