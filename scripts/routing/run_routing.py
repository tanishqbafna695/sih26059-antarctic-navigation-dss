"""CLI runner for Phase 12 multi-objective route optimization (FR-22/23/24).

Generates Fastest / Safest / Balanced routes for each vessel preset on the
Bharati -> Maitri corridor, evaluates the Phase 5 shortest-path baseline on
the SAME time-aware cost ledger for comparison, and writes data/routing/latest.json.

Usage:
    python scripts/routing/run_routing.py [--depart-day 0] [--store PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import xarray as xr

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.baselines import routing as baseline_routing  # noqa: E402
from backend.routing import NoRouteFound, plan_routes  # noqa: E402
from backend.routing.costs import DayFieldsCache  # noqa: E402
from backend.routing.optimizer import _reference_scales, evaluate_path_metrics  # noqa: E402
from backend.vessel import VesselRegistry  # noqa: E402

BHARATI = (-69.41, 76.19)
MAITRI = (-70.77, 11.73)
DEFAULT_STORE = REPO_ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"

# ASSUMED demo iceberg fixes along the corridor (positions chosen near the
# route domain; advected + uncertainty-grown by the Phase 7 model in costs.py).
SAMPLE_ICEBERGS = [
    {"lon": 70.0, "lat": -68.0, "uncertainty_km": 2.0,
     "v_east_kmh": 0.4, "v_north_kmh": -0.1, "obs_staleness_h": 6.0},
    {"lon": 45.0, "lat": -67.5, "uncertainty_km": 4.0,
     "v_east_kmh": 0.6, "v_north_kmh": 0.0, "obs_staleness_h": 6.0},
]


def baseline_with_metrics(ds: xr.Dataset, profile, depart_day: int,
                          icebergs) -> dict:
    """Shortest-path baseline (FR-21) scored on the same time-aware ledger."""
    base = baseline_routing.baseline_route_from_store(
        ds, depart_day, BHARATI, MAITRI, max_sic=float(profile.max_sic_limit))
    if not base["found"]:
        return {"found": False, "reason": base.get("reason", "no path")}
    spacing = float(ds.attrs.get("spacing_km", 25.0))
    t_ref, f_ref = _reference_scales(profile, spacing)
    cache = DayFieldsCache(ds, profile, None, icebergs, depart_day)
    path_xy = [tuple(p) for p in base["path_xy"]]
    metrics = evaluate_path_metrics(cache, path_xy, t_ref, f_ref)
    return {"found": True, "distance_km": round(base["distance_km"], 1),
            "n_cells": base["n_cells"], **metrics}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Phase 12 route optimization")
    ap.add_argument("--depart-day", type=int, default=0)
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--out", default=str(REPO_ROOT / "data" / "routing"))
    args = ap.parse_args(argv)

    print("=== SIH26059 Phase 12 — Multi-Objective Route Optimization ===")
    ds = xr.open_dataset(args.store, engine="h5netcdf")
    print(f"store: {args.store}  ({dict(ds.sizes)})")

    registry = VesselRegistry()
    report = {"phase": 12, "depart_day_index": args.depart_day,
              "from": {"name": "Bharati", "lat": BHARATI[0], "lon": BHARATI[1]},
              "to": {"name": "Maitri", "lat": MAITRI[0], "lon": MAITRI[1]},
              "icebergs_assumed": SAMPLE_ICEBERGS,
              "vessels": {}}

    for vid in ("open_water_rv", "polar_class_pc7", "polar_class_pc1"):
        prof = registry.get_profile(vid)
        print(f"\n--- {prof.name} (SIC limit {prof.max_sic_limit * 100:.0f}%) ---")
        try:
            plan = plan_routes(ds, BHARATI, MAITRI, prof,
                               depart_day_index=args.depart_day,
                               icebergs=SAMPLE_ICEBERGS)
        except NoRouteFound as e:
            print(f"  NO ROUTE: {e} {e.details}")
            report["vessels"][vid] = {"found": False, "reason": str(e),
                                      "details": e.details}
            continue
        base = baseline_with_metrics(ds, prof, args.depart_day, SAMPLE_ICEBERGS)
        plan["baseline_shortest_path"] = base
        # strip full polylines from the saved report except cell counts? keep
        # path_xy (needed for Phase 13 trade-off + map overlay); drop lat/lon
        # duplicates to keep the JSON lean
        for r in plan["routes"].values():
            r.pop("path", None)
        report["vessels"][vid] = plan

        hdr = f"  {'route':<10} {'time_h':>8} {'fuel_L':>9} {'risk':>7} {'max_risk':>8} {'ice_exp':>7} {'cells':>6}"
        print(hdr)
        for name, r in plan["routes"].items():
            print(f"  {name:<10} {r['travel_time_h']:>8.1f} {r['fuel_liters']:>9.0f} "
                  f"{r['mean_hazard']:>7.3f} {r['max_hazard']:>8.3f} "
                  f"{r['ice_exposure_frac']:>7.2f} {r['n_cells']:>6}")
        if base.get("found"):
            print(f"  {'baseline':<10} {base['travel_time_h']:>8.1f} {base['fuel_liters']:>9.0f} "
                  f"{base['mean_hazard']:>7.3f} {base['max_hazard']:>8.3f} "
                  f"{base['ice_exposure_frac']:>7.2f} {base['n_cells']:>6}")
        print(f"  confidence: {plan['confidence']['overall_confidence']:.2f} "
              f"({plan['confidence']['status_label']})  ocean: {plan['ocean_source_day0']}")

    ds.close()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved routing report to: {out_path}")


if __name__ == "__main__":
    main()
