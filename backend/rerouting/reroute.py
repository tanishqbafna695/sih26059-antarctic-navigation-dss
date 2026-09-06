"""Dynamic re-routing engine (FR-30, FR-31, FR-32, Phase 15).

Decision framing (the honest comparison): when new observations arrive, the
old advice is re-scored as "what staying the course costs IN THE NEW WORLD"
(remaining old path evaluated under new fields) versus freshly optimized
routes from the vessel's current position. Outcomes:
- RE-ROUTE: a different route is now advised,
- ADJUSTED: same winner, but its path moved,
- HOLDS: identical path still optimal (reported, never hidden).

Trigger thresholds (FR-32, configurable): berg-fix moves, corridor SIC
shifts and remaining-path hazard jumps are detected and listed; the chain
recomputes regardless (FR-30), the notice states the outcome either way
(FR-31/OUT-6). A mid-voyage iceberg fix is an OBSERVED update when supplied
by the caller; scenario-injected fixes must be labeled ASSUMED upstream.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import xarray as xr

from backend.baselines.metrics import haversine_km
from backend.explanation import explain_change, explain_recommendation
from backend.routing.costs import DayFieldsCache, WEIGHT_PRESETS
from backend.routing.optimizer import (
    NoRouteFound,
    _reference_scales,
    arrival_times,
    evaluate_path_metrics,
    time_dependent_dijkstra,
)
from backend.tradeoff import recommend
from backend.uncertainty.engine import compute_combined_confidence


@dataclass
class RerouteThresholds:
    """Configurable trigger thresholds (FR-32)."""
    min_berg_move_km: float = 10.0
    min_sic_delta: float = 0.05
    min_hazard_delta: float = 0.02


def _row_from_metrics(name: str, m: Dict[str, Any], conf: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "route": name, "origin": "reroute_replan",
        "travel_time_h": float(m["travel_time_h"]),
        "fuel_liters": float(m["fuel_liters"]),
        "mean_hazard": float(m["mean_hazard"]),
        "max_hazard": float(m["max_hazard"]),
        "ice_exposure_frac": float(m["ice_exposure_frac"]),
        "mean_iceberg_hazard": float(m.get("mean_iceberg_hazard", 0.0)),
        "distance_km": float(m["distance_km"]),
        "n_cells": int(m["n_cells"]),
        "confidence": float(conf["overall_confidence"]),
        "confidence_label": conf["status_label"],
        "confidence_shared_across_routes": True,
    }


def detect_changes(old_fields: Dict[str, Any], new_fields: Dict[str, Any],
                   remaining_path: List[Tuple[int, int]],
                   old_icebergs: List[Dict[str, Any]],
                   new_icebergs: List[Dict[str, Any]],
                   thresholds: RerouteThresholds) -> Dict[str, Any]:
    """Compare old vs new conditions along the remaining path cells."""
    ys = np.array([y for y, _ in remaining_path])
    xs = np.array([x for _, x in remaining_path])
    sic_delta = float(np.mean(np.abs(new_fields["sic"][ys, xs]
                                          - old_fields["sic"][ys, xs])))
    hz_delta = float(np.max(new_fields["berg_hazard"][ys, xs]
                            - old_fields["berg_hazard"][ys, xs]))
    moves = []
    for i, (ob, nb) in enumerate(zip(old_icebergs, new_icebergs)):
        d = haversine_km(float(ob["lon"]), float(ob["lat"]),
                         float(nb["lon"]), float(nb["lat"]))
        moves.append({"berg_index": i, "move_km": round(d, 1)})
    big_moves = [m for m in moves if m["move_km"] >= thresholds.min_berg_move_km]
    triggers = []
    if len(new_icebergs) > len(old_icebergs):
        triggers.append(f"{len(new_icebergs) - len(old_icebergs)} new iceberg "
                        f"fix(es) appeared")
    if big_moves:
        triggers.append(f"{len(big_moves)} iceberg fix(es) moved "
                        f">= {thresholds.min_berg_move_km} km")
    if sic_delta >= thresholds.min_sic_delta:
        triggers.append(f"corridor sea-ice shift {sic_delta:.3f} "
                        f">= {thresholds.min_sic_delta}")
    if hz_delta >= thresholds.min_hazard_delta:
        triggers.append(f"iceberg-danger jump {hz_delta:.3f} on remaining path "
                        f">= {thresholds.min_hazard_delta}")
    return {
        "sic_delta_mean": round(sic_delta, 4),
        "berg_hazard_increase_max": round(hz_delta, 4),
        "berg_moves_km": moves,
        "triggered": bool(triggers),
        "triggers": triggers,
        "trigger_text": ("; ".join(triggers) if triggers
                         else "no change above configured thresholds"),
    }


def reroute(ds: xr.Dataset, profile, old_winner_path: List[Tuple[int, int]],
            old_winner_name: str, old_depart_day: int,
            old_icebergs: List[Dict[str, Any]], elapsed_h: float,
            new_depart_day: int, new_icebergs: List[Dict[str, Any]],
            thresholds: Optional[RerouteThresholds] = None,
            priority: str = "balanced",
            vessel: Optional[Dict[str, Any]] = None,
            spacing_km: Optional[float] = None,
            frozen_day_index: Optional[int] = None,
            staleness_h: float = 0.0,
            extra_missing_inputs: Optional[List[str]] = None) -> Dict[str, Any]:
    """Recompute the decision mid-voyage and emit the OUT-6 notice (FR-31).

    old_winner_path: advised path cell list from the original plan.
    elapsed_h: hours already sailed along it. The vessel's current cell is
    located by arrival time; the remainder is re-scored under NEW fields.
    frozen_day_index (Phase 16 SC-4): cap the new cache at this dataset day
    to model a SIMULATED observation outage (last-observation persistence);
    pair with staleness_h + extra_missing_inputs so confidence degrades
    honestly instead of silently.
    """
    thresholds = thresholds or RerouteThresholds()
    spacing = spacing_km or float(ds.attrs.get("spacing_km", 25.0))
    t_ref, f_ref = _reference_scales(profile, spacing)

    old_cache = DayFieldsCache(ds, profile, None, old_icebergs, old_depart_day)
    times = arrival_times(old_cache, [tuple(p) for p in old_winner_path])
    if elapsed_h >= times[-1]:
        return {"recomputed": True, "outcome": "COMPLETE",
                "notice": "vessel already arrived; no re-route needed."}
    idx = next(i for i, t in enumerate(times) if t > elapsed_h) - 1
    idx = max(0, idx)
    current = tuple(old_winner_path[idx])
    remaining = [tuple(p) for p in old_winner_path[idx:]]

    new_cache = DayFieldsCache(ds, profile, None, new_icebergs, new_depart_day,
                               max_day_index=frozen_day_index)
    old_fields_now = old_cache.day(elapsed_h)
    new_fields_now = new_cache.day(0.0)
    changes = detect_changes(old_fields_now, new_fields_now, remaining,
                             old_icebergs, new_icebergs, thresholds)

    # cost of staying the course, evaluated IN THE NEW WORLD
    old_remaining = evaluate_path_metrics(new_cache, remaining, t_ref, f_ref)

    # fresh optimization from the current cell (cell-direct: no snapping jump)
    goal = tuple(old_winner_path[-1])
    weights = WEIGHT_PRESETS
    try:
        new_searches = {n: time_dependent_dijkstra(new_cache, current, goal, w, t_ref, f_ref)
                        for n, w in weights.items()}
    except NoRouteFound as e:
        return {"recomputed": True, "outcome": "NO_ROUTE",
                "current_cell": [int(current[0]), int(current[1])],
                "changes": changes,
                "notice": f"re-route impossible: {e}",
                "details": e.details,
                "old_remaining_if_staying": old_remaining}

    new_metrics = {n: evaluate_path_metrics(new_cache, s["path_xy"], t_ref, f_ref)
                   for n, s in new_searches.items()}
    longest_h = max(m["travel_time_h"] for m in new_metrics.values())
    missing = [] if "uo" in ds else ["glorys12_ocean_current (wind-driven fallback active)"]
    missing = list(missing) + list(extra_missing_inputs or [])
    staleness = max(0.0, float(staleness_h))
    conf = compute_combined_confidence(
        horizon_h=longest_h, staleness_h=staleness, missing_inputs=missing,
        provenance_sources=["OSI-SAF", "ERA5", "GLORYS12-fallback"]).to_dict()
    rows = [_row_from_metrics(n, new_metrics[n], conf) for n in weights]
    comp = {"vessel_id": getattr(profile, "vessel_id", "unknown"),
            "routes_available": True, "rows": rows, "confidence": conf}
    rec = recommend(comp, priority)
    new_winner = rec["recommended"]

    if new_winner != old_winner_name:
        outcome = "RE-ROUTE"
    elif ([list(p) for p in new_searches[new_winner]["path_xy"]]
            != [list(p) for p in remaining]):
        outcome = "ADJUSTED"
    else:
        # identical path under identical deterministic walk -> HOLDS
        outcome = "HOLDS"

    nw = new_metrics[new_winner]
    change = explain_change(
        {"recommended": f"{old_winner_name} (remaining course)",
         "travel_time_h": round(old_remaining["travel_time_h"], 2),
         "fuel_liters": round(old_remaining["fuel_liters"], 1),
         "mean_hazard": round(old_remaining["mean_hazard"], 4)},
        {"recommended": new_winner,
         "travel_time_h": round(nw["travel_time_h"], 2),
         "fuel_liters": round(nw["fuel_liters"], 1),
         "mean_hazard": round(nw["mean_hazard"], 4)},
        trigger=changes["trigger_text"])
    vessel = vessel or {"name": getattr(profile, "name", "Vessel"),
                        "ice_class": getattr(profile, "ice_class", "unknown"),
                        "max_sic_limit": float(profile.max_sic_limit)}
    new_explanation = explain_recommendation(rows, rec, vessel)

    try:
        new_day = str(np.datetime64(ds["time"].values[new_depart_day], "D"))
    except Exception:
        new_day = str(ds["time"].values[new_depart_day])
    return {
        "recomputed": True,
        "outcome": outcome,
        "current_cell": [int(current[0]), int(current[1])],
        "elapsed_h": round(float(elapsed_h), 1),
        "new_depart_day": int(new_depart_day),
        "new_date": new_day,
        "staleness_h": staleness,
        "frozen_day_index": frozen_day_index,
        "changes": changes,
        "old_remaining_if_staying": old_remaining,
        "new_routes": {n: {**new_metrics[n],
                           "path_xy": new_searches[n]["path_xy"]}
                       for n in weights},
        "new_recommendation": rec,
        "change_explanation": change,
        "new_explanation": new_explanation,
        "confidence": conf,
    }
