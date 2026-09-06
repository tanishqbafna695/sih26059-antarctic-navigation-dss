"""Departure-matrix backtest harness (SC-1, SC-2, SC-6, SC-7, Phase 16).

For each (vessel, depart-day) pair the full Phase 12+13 chain runs
(plan -> compare -> balanced recommendation); NoRouteFound is recorded as
an honest data point, never an exception. summarize_matrix() then extracts
the acceptance evidence: success rates, same-day vessel differences (SC-6)
and the no-route ledger (SC-7).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import xarray as xr

from backend.routing import NoRouteFound, plan_routes
from backend.tradeoff import build_comparison, recommend
from backend.vessel import VesselRegistry

BHARATI = (-69.41, 76.19)
MAITRI = (-70.77, 11.73)


def run_departure_matrix(ds: xr.Dataset, pairs: List[Tuple[str, int]],
                         icebergs: Optional[List[Dict[str, Any]]] = None
                         ) -> Dict[str, Any]:
    """Run the chain for explicit (vessel_id, depart_day) pairs.

    Returns {"entries": {(vid, day): {...}}, ...} with either
    {found True, winner, time_h, fuel, risk} or {found False, reason}.
    """
    registry = VesselRegistry()
    entries: Dict[str, Any] = {}
    for vid, day in pairs:
        prof = registry.get_profile(vid)
        key = f"{vid}@{day}"
        try:
            plan = plan_routes(ds, BHARATI, MAITRI, prof,
                               depart_day_index=int(day),
                               icebergs=icebergs or [])
        except NoRouteFound as e:
            entries[key] = {"vessel_id": vid, "depart_day": int(day),
                            "found": False, "reason": str(e),
                            "details": e.details}
            continue
        comp = build_comparison(plan)
        rec = recommend(comp, "balanced")
        w = plan["routes"][rec["recommended"]]
        entries[key] = {"vessel_id": vid, "depart_day": int(day),
                        "found": True, "winner": rec["recommended"],
                        "time_h": w["travel_time_h"],
                        "fuel_liters": w["fuel_liters"],
                        "mean_hazard": w["mean_hazard"]}
    return {"pairs": [f"{v}@{d}" for v, d in pairs], "entries": entries}


def summarize_matrix(matrix: Dict[str, Any]) -> Dict[str, Any]:
    """Acceptance summary: success rate, SC-6 differences, SC-7 ledger."""
    entries = matrix["entries"]
    n = len(entries)
    n_ok = sum(1 for e in entries.values() if e["found"])
    by_day: Dict[int, Dict[str, Any]] = {}
    for e in entries.values():
        by_day.setdefault(e["depart_day"], {})[e["vessel_id"]] = e
    sc6, sc7 = [], []
    for day, per_vessel in sorted(by_day.items()):
        outcomes = {v: e["found"] for v, e in per_vessel.items()}
        if len(set(outcomes.values())) > 1:  # same day, different answers
            sc6.append({"depart_day": day, "outcomes": outcomes,
                        "note": "same environment + different vessel = "
                                "different answer (FR-20)"})
        for v, e in per_vessel.items():
            if not e["found"]:
                sc7.append({"vessel_id": v, "depart_day": day,
                            "reason": e["reason"]})
    return {
        "n_cases": n,
        "n_success": n_ok,
        "success_rate": round(n_ok / n, 3) if n else 0.0,
        "sc6_vessel_differences": sc6,
        "sc7_no_route_ledger": sc7,
    }
