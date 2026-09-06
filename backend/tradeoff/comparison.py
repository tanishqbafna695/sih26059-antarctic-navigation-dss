"""Trade-off comparison table (FR-25, Phase 13).

Builds the master-brief §6 comparison from a Phase 12 vessel plan: one row
per route (fastest / safest / balanced, plus the shortest-path baseline when
it was found) over time, fuel, risk, ice exposure, iceberg exposure and
confidence. Every number comes from the recorded plan; nothing is estimated
here.

Confidence note (honest): the Phase 12 confidence report is SET-level (one
horizon = longest travel time for the whole route set), so every row shares
it. It is flagged as shared, never presented as per-route precision.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Metrics compared across routes (FR-25). All are lower-is-better except
# confidence, which is carried as a shared qualifier, not a scored metric.
COMPARE_METRICS = ("travel_time_h", "fuel_liters", "mean_hazard",
                   "max_hazard", "ice_exposure_frac", "mean_iceberg_hazard",
                   "distance_km")

ROW_LABELS = ("fastest", "safest", "balanced")


def _row_from_metrics(name: str, m: Dict[str, Any], confidence: Dict[str, Any],
                      origin: str) -> Dict[str, Any]:
    return {
        "route": name,
        "origin": origin,  # "multiobjective" or "shortest_path_baseline"
        "travel_time_h": float(m["travel_time_h"]),
        "fuel_liters": float(m["fuel_liters"]),
        "mean_hazard": float(m["mean_hazard"]),
        "max_hazard": float(m["max_hazard"]),
        "ice_exposure_frac": float(m["ice_exposure_frac"]),
        "mean_iceberg_hazard": float(m.get("mean_iceberg_hazard", 0.0)),
        "distance_km": float(m["distance_km"]),
        "n_cells": int(m["n_cells"]),
        # shared set-level qualifier (see module docstring)
        "confidence": float(confidence["overall_confidence"]),
        "confidence_label": confidence["status_label"],
        "confidence_shared_across_routes": True,
    }


def build_comparison(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Build the comparison table for one vessel plan.

    Returns {"vessel_id", "depart_date", "rows": [...], "baseline_included",
    "confidence": {...}}. Plans with found=False (FR-24 no-route) yield
    {"routes_available": False, "reason": ...} — never an empty table.
    """
    if not plan.get("routes"):
        return {"vessel_id": plan.get("vessel_id", "unknown"),
                "routes_available": False,
                "reason": plan.get("reason", "no acceptable route found "
                                   "under current constraints"),
                "details": plan.get("details", {})}
    conf = plan.get("confidence", {"overall_confidence": float("nan"),
                                   "status_label": "UNKNOWN"})
    rows: List[Dict[str, Any]] = [
        _row_from_metrics(name, plan["routes"][name], conf, "multiobjective")
        for name in ROW_LABELS if name in plan["routes"]
    ]
    baseline_included = False
    base = plan.get("baseline_shortest_path") or {}
    if base.get("found"):
        rows.append(_row_from_metrics("baseline_shortest_path", base, conf,
                                      "shortest_path_baseline"))
        baseline_included = True
    return {
        "vessel_id": plan.get("vessel_id", "unknown"),
        "depart_date": plan.get("depart_date", "unknown"),
        "routes_available": True,
        "rows": rows,
        "baseline_included": baseline_included,
        "confidence": conf,
    }


def comparison_markdown(comp: Dict[str, Any]) -> str:
    """Render the master-brief §6 table (for logs/demo; values from comp)."""
    if not comp.get("routes_available"):
        return f"| no routes | {comp.get('reason')} |"
    lines = ["| Route | Time (h) | Fuel (L) | Risk | Max risk | Ice exp | Berg hz | Conf |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in comp["rows"]:
        lines.append(
            f"| {r['route']} | {r['travel_time_h']:.1f} | {r['fuel_liters']:.0f} | "
            f"{r['mean_hazard']:.3f} | {r['max_hazard']:.3f} | "
            f"{r['ice_exposure_frac']:.2f} | {r['mean_iceberg_hazard']:.3f} | "
            f"{r['confidence']:.2f} ({r['confidence_label']}) |")
    return "\n".join(lines)
