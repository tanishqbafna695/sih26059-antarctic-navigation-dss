"""CLI runner for Phase 15 dynamic re-routing (FR-30, FR-31, FR-32).

Scenario (real data, Bharati -> Maitri, PC7): the vessel sails the advised
day-45 route for 120 h. At day 50 two updates are evaluated:
  A. CONTROL — new day's real observations only (no new iceberg fixes).
  B. SC-5 INJECTION — plus one ASSUMED fresh iceberg fix placed on the
     remaining course (labeled ASSUMED; a real fix would arrive the same way).
Each case recomputes from the vessel's current position and emits the OUT-6
notice (old remaining course vs new advice + trigger + change explanation).

Usage:
    python scripts/rerouting/run_reroute.py [--elapsed-h 120] [--new-day 50]
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

from backend.rerouting import RerouteThresholds, reroute  # noqa: E402
from backend.vessel import VesselRegistry  # noqa: E402

DEFAULT_STORE = REPO_ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"
DEFAULT_ROUTING = REPO_ROOT / "data" / "routing" / "latest.json"
DEFAULT_TRADEOFF = REPO_ROOT / "data" / "tradeoff" / "latest.json"
VESSEL_ID = "polar_class_pc7"
OLD_DAY = 45


def _print_notice(title: str, notice: dict) -> None:
    print(f"\n=== {title} ===")
    print(f"outcome: {notice.get('outcome')}")
    if notice.get("outcome") in ("COMPLETE", "NO_ROUTE"):
        print(notice.get("notice"))
        return
    ch = notice["changes"]
    print(f"trigger check: {ch['trigger_text']}")
    old = notice["old_remaining_if_staying"]
    nw = notice["new_routes"][notice["new_recommendation"]["recommended"]]
    print(f"stay-the-course (new world): {old['travel_time_h']:.1f} h, "
          f"{old['fuel_liters']:.0f} L, risk {old['mean_hazard']:.3f}")
    print(f"new advice ({notice['new_recommendation']['recommended']}): "
          f"{nw['travel_time_h']:.1f} h, {nw['fuel_liters']:.0f} L, "
          f"risk {nw['mean_hazard']:.3f}")
    print(f"[change]\n{notice['change_explanation']['text']}")
    print(f"[new advice, why]\n{notice['new_explanation']['headline']}")
    for s in notice["new_explanation"]["strengths"][:3]:
        print(f"  - {s}")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Phase 15 dynamic re-routing")
    ap.add_argument("--elapsed-h", type=float, default=120.0)
    ap.add_argument("--new-day", type=int, default=50)
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--routing", default=str(DEFAULT_ROUTING))
    ap.add_argument("--tradeoff", default=str(DEFAULT_TRADEOFF))
    ap.add_argument("--out", default=str(REPO_ROOT / "data" / "rerouting"))
    args = ap.parse_args(argv)

    print("=== SIH26059 Phase 15 — Dynamic Re-Routing ===")
    ds = xr.open_dataset(args.store, engine="h5netcdf")
    routing = json.loads(Path(args.routing).read_text(encoding="utf-8"))
    tradeoff = json.loads(Path(args.tradeoff).read_text(encoding="utf-8"))
    prof = VesselRegistry().get_profile(VESSEL_ID)

    vessel_plan = routing["vessels"][VESSEL_ID]
    old_winner = tradeoff["vessels"][VESSEL_ID]["recommendations"]["balanced"]["recommended"]
    old_path = vessel_plan["routes"][old_winner]["path_xy"]
    old_bergs = routing.get("icebergs_assumed", [])
    print(f"vessel: {prof.name} | old advice ({old_winner}, day {OLD_DAY}) | "
          f"sailed {args.elapsed_h:.0f} h | update day {args.new_day}")

    # remaining-path midpoint -> lon/lat for the SC-5 injection
    lat2d = np.asarray(ds["lat"].values)
    lon2d = np.asarray(ds["lon"].values)
    mid = old_path[len(old_path) // 2]
    mid_lon, mid_lat = float(lon2d[mid[0], mid[1]]), float(lat2d[mid[0], mid[1]])

    injected = {"lon": round(mid_lon, 2), "lat": round(mid_lat, 2),
                "uncertainty_km": 2.0, "v_east_kmh": 0.0, "v_north_kmh": 0.0,
                "obs_staleness_h": 0.0, "source": "ASSUMED-scenario-injection"}
    cases = {
        "A. CONTROL (observations only)": list(old_bergs),
        "B. SC-5 (fresh iceberg fix on course, ASSUMED)": list(old_bergs) + [injected],
    }
    report = {"phase": 15, "vessel_id": VESSEL_ID, "old_winner": old_winner,
              "old_depart_day": OLD_DAY, "elapsed_h": args.elapsed_h,
              "new_depart_day": args.new_day,
              "injected_fix_assumed": injected, "cases": {}}
    for title, bergs in cases.items():
        notice = reroute(ds, prof, old_path, old_winner, OLD_DAY, old_bergs,
                         args.elapsed_h, args.new_day, bergs,
                         RerouteThresholds(), priority="balanced")
        _print_notice(title, notice)
        report["cases"][title] = notice

    ds.close()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved re-routing report to: {out_path}")


if __name__ == "__main__":
    main()
