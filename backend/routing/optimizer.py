"""Time-aware multi-objective route search (FR-22, FR-23, FR-24, Phase 12).

ALGORITHM — time-dependent label-setting Dijkstra over the 8-connectivity
grid graph (same topology as the Phase 5 shortest-path baseline, FR-21, so
routes are directly comparable):

- State per node: best composite cost g(n) + earliest arrival time t(n).
- Edge u->v is evaluated with the DayFields of the ARRIVAL day
  (depart_day + t(u) mapped to a dataset day, clamped to the store range).
  This is FR-23: route costs use the forecast hazard at the time the vessel
  actually transits each cell.
- Per directed edge:
      along_current = (uo[v]*sin(hdg) + vo[v]*cos(hdg)) * KTS_PER_MS
      V_eff   = max(0.5, base_speed[v] + along_current)   [vessel.performance]
      time_h  = dist_km(u,v) / V_eff
      fuel_L  = fuel_rate(V_eff, sic[v], bft[v]) * time_h [vessel.performance]
      risk    = hazard_total[v]
      edge_cost = a*risk + b*(time_h/T_ref) + g*(fuel_L/F_ref)
  Blocked target cells (hard constraints) are never relaxed.
- T_ref/F_ref normalize time/fuel to O(1): crossing one reference cell
  (spacing_km, default 25) at cruise speed on base fuel. Documented so the
  weights a/b/g are interpretable across vessels.
- FIFO NOTE (honest limitation): arrival-time propagation is exact under the
  FIFO property (traversal times non-negative; no waiting allowed). The
  composite-cost label-setting is the standard time-dependent Dijkstra
  heuristic for non-static costs: optimal for arrival time, near-optimal for
  the weighted cost. Recorded as an ASSUMED limitation in the gate log.

NO-ROUTE (FR-24/OUT-8): if the goal is unreachable, raise NoRouteFound with
blocking statistics (fraction of domain blocked, nearest reachable distance
to goal) — the caller converts this to the OUT-8 statement. Never a fake route.
"""
from __future__ import annotations

import heapq
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import xarray as xr

from backend.baselines.metrics import haversine_km
from backend.baselines.routing import navigable_mask, nearest_valid_cell

from .costs import WEIGHT_PRESETS, DayFieldsCache

_KTS_TO_KMH = 1.852
_KTS_PER_MS = 1.94384
_MOVES = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]


class NoRouteFound(Exception):
    """Raised when no acceptable route exists (FR-24). Carries OUT-8 details."""

    def __init__(self, reason: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(reason)
        self.details = details or {}


def fuel_rate_for(profile, speed_kts: float, sic: float, beaufort: int) -> float:
    """Scalar fuel model mirroring vessel.performance.calculate_fuel_rate."""
    sp = max(0.10, float(speed_kts))
    sic_val = max(0.0, min(1.0, float(sic)))
    v_cruise = float(profile.cruise_speed_kts)
    sic_lim = max(0.05, float(profile.max_sic_limit))
    f_base = float(profile.base_fuel_rate_lph)
    f_max = float(profile.max_fuel_rate_lph)
    l_speed = (sp / v_cruise) ** 2.2
    if 0.0 < sic_val <= sic_lim:
        l_ice = 1.0 + 1.20 * ((sic_val / sic_lim) ** 1.5)
    elif sic_val > sic_lim:
        l_ice = 2.20
    else:
        l_ice = 1.0
    l_wx = 1.0 + 0.02 * max(0, int(beaufort))
    return float(min(f_max, max(f_base * 0.20, f_base * l_speed * l_ice * l_wx)))


def _reference_scales(profile, spacing_km: float = 25.0) -> Tuple[float, float]:
    """T_ref (h) and F_ref (L) for one reference cell at cruise/base fuel."""
    t_ref = spacing_km / (float(profile.cruise_speed_kts) * _KTS_TO_KMH)
    f_ref = float(profile.base_fuel_rate_lph) * t_ref
    return max(t_ref, 1e-6), max(f_ref, 1e-6)


def time_dependent_dijkstra(cache: DayFieldsCache, start: Tuple[int, int],
                            goal: Tuple[int, int], weights: Dict[str, float],
                            t_ref: float, f_ref: float,
                            max_elapsed_h: float = 24 * 60.0) -> Dict[str, Any]:
    """Search from start to goal cell. Returns path + arrival ledger.

    Raises NoRouteFound when the goal is unreachable.
    """
    profile = cache.profile
    ds = cache.ds
    lat2d = np.asarray(ds["lat"].values)
    lon2d = np.asarray(ds["lon"].values)
    ny, nx = lat2d.shape
    alpha, beta, gamma = float(weights["alpha"]), float(weights["beta"]), float(weights["gamma"])

    day0 = cache.day(0.0)
    if bool(day0["blocked"][start]):
        raise NoRouteFound("start cell is blocked under vessel constraints",
                           {"cell": start})
    if bool(day0["blocked"][goal]):
        # still attempt: snap check happens in plan_routes; here report directly
        raise NoRouteFound("goal cell is blocked under vessel constraints",
                           {"cell": goal})

    INF = float("inf")
    g = np.full((ny, nx), INF)
    arrival = np.full((ny, nx), INF)
    visited = np.zeros((ny, nx), dtype=bool)
    parent_y = np.full((ny, nx), -1, dtype=np.int32)
    parent_x = np.full((ny, nx), -1, dtype=np.int32)
    g[start] = 0.0
    arrival[start] = 0.0
    heap: list[tuple[float, int, int]] = [(0.0, start[0], start[1])]
    expanded = 0

    while heap:
        cost_u, uy, ux = heapq.heappop(heap)
        if visited[uy, ux]:
            continue
        visited[uy, ux] = True
        expanded += 1
        if (uy, ux) == (goal[0], goal[1]):
            break
        t_u = float(arrival[uy, ux])
        if t_u > max_elapsed_h:
            continue
        for dy, dx in _MOVES:
            vy, vx = uy + dy, ux + dx
            if not (0 <= vy < ny and 0 <= vx < nx) or visited[vy, vx]:
                continue
            # arrival day fields: hazard/speed evaluated when we get there (FR-23)
            dist_km = haversine_km(lon2d[uy, ux], lat2d[uy, ux], lon2d[vy, vx], lat2d[vy, vx])
            # provisional arrival for the day lookup (uses target base speed w/o current)
            fields = cache.day(t_u)
            if bool(fields["blocked"][vy, vx]):
                continue
            base_v = float(fields["base_speed_kts"][vy, vx])
            if base_v <= 0.0:
                continue
            # along-track current at the target cell (kts)
            hdg = math.atan2(lon2d[vy, vx] - lon2d[uy, ux],
                             lat2d[vy, vx] - lat2d[uy, ux])
            along_kts = (float(fields["uo"][vy, vx]) * math.sin(hdg)
                         + float(fields["vo"][vy, vx]) * math.cos(hdg)) * _KTS_PER_MS
            v_eff = max(0.50, base_v + along_kts)
            time_h = dist_km / v_eff
            t_v = t_u + time_h
            f_now = cache.day(t_v)  # re-evaluate at true arrival day (FR-23)
            if bool(f_now["blocked"][vy, vx]):
                continue
            risk = float(f_now["hazard_total"][vy, vx])
            fuel = fuel_rate_for(profile, v_eff, float(f_now["sic"][vy, vx]),
                                 int(f_now["beaufort"][vy, vx])) * time_h
            edge = alpha * risk + beta * (time_h / t_ref) + gamma * (fuel / f_ref)
            g_v = cost_u + edge
            if g_v < g[vy, vx]:
                g[vy, vx] = g_v
                arrival[vy, vx] = t_v
                parent_y[vy, vx] = uy
                parent_x[vy, vx] = ux
                heapq.heappush(heap, (g_v, vy, vx))

    gy, gx = goal
    if not visited[gy, gx]:
        # OUT-8 diagnostics: how much of the domain is blocked, how close did we get?
        d0 = cache.day(0.0)
        blocked_frac = float(np.mean(d0["blocked"]))
        # nearest visited cell to goal (in km) for the "next-reassessment" hint
        vys, vxs = np.where(visited)
        if len(vys):
            dkm = [haversine_km(lon2d[y, x], lat2d[y, x], lon2d[gy, gx], lat2d[gy, gx])
                   for y, x in zip(vys.tolist(), vxs.tolist())]
            nearest_km = float(min(dkm))
        else:
            nearest_km = float("inf")
        raise NoRouteFound(
            "no acceptable route found under current constraints",
            {"blocked_fraction": round(blocked_frac, 4),
             "nearest_reachable_km_to_goal": round(nearest_km, 1),
             "cells_expanded": int(expanded)})

    # reconstruct path goal -> start
    path_xy: List[Tuple[int, int]] = [(gy, gx)]
    while path_xy[-1] != (start[0], start[1]):
        cy, cx = path_xy[-1]
        path_xy.append((int(parent_y[cy, cx]), int(parent_x[cy, cx])))
    path_xy.reverse()
    return {"path_xy": path_xy, "total_cost": float(g[gy, gx]),
            "arrival_h": float(arrival[gy, gx]), "cells_expanded": int(expanded)}


def arrival_times(cache: DayFieldsCache, path_xy: List[Tuple[int, int]]) -> List[float]:
    """Cumulative arrival hours at each path cell (arrival[0] == 0.0).

    Same per-leg speed rule as the search and evaluate_path_metrics
    (Phase 15 uses this to locate the vessel mid-voyage).
    """
    ds = cache.ds
    lat2d = np.asarray(ds["lat"].values)
    lon2d = np.asarray(ds["lon"].values)
    times = [0.0]
    t = 0.0
    for (uy, ux), (vy, vx) in zip(path_xy[:-1], path_xy[1:]):
        dist_km = haversine_km(lon2d[uy, ux], lat2d[uy, ux], lon2d[vy, vx], lat2d[vy, vx])
        fields = cache.day(t)
        hdg = math.atan2(lon2d[vy, vx] - lon2d[uy, ux], lat2d[vy, vx] - lat2d[uy, ux])
        along_kts = (float(fields["uo"][vy, vx]) * math.sin(hdg)
                     + float(fields["vo"][vy, vx]) * math.cos(hdg)) * _KTS_PER_MS
        v_eff = max(0.50, float(fields["base_speed_kts"][vy, vx]) + along_kts)
        t += dist_km / v_eff
        times.append(t)
    return times


def evaluate_path_metrics(cache: DayFieldsCache, path_xy: List[Tuple[int, int]],
                          t_ref: float, f_ref: float) -> Dict[str, Any]:
    """Walk a found path recomputing time/fuel/hazard per leg (deterministic)."""
    profile = cache.profile
    ds = cache.ds
    lat2d = np.asarray(ds["lat"].values)
    lon2d = np.asarray(ds["lon"].values)
    total_km = 0.0
    total_h = 0.0
    total_fuel = 0.0
    risks, sics, bergs = [], [], []
    max_risk = 0.0
    t = 0.0
    for (uy, ux), (vy, vx) in zip(path_xy[:-1], path_xy[1:]):
        dist_km = haversine_km(lon2d[uy, ux], lat2d[uy, ux], lon2d[vy, vx], lat2d[vy, vx])
        fields = cache.day(t)
        hdg = math.atan2(lon2d[vy, vx] - lon2d[uy, ux], lat2d[vy, vx] - lat2d[uy, ux])
        along_kts = (float(fields["uo"][vy, vx]) * math.sin(hdg)
                     + float(fields["vo"][vy, vx]) * math.cos(hdg)) * _KTS_PER_MS
        v_eff = max(0.50, float(fields["base_speed_kts"][vy, vx]) + along_kts)
        time_h = dist_km / v_eff
        t += time_h
        f_now = cache.day(t)
        fuel = fuel_rate_for(profile, v_eff, float(f_now["sic"][vy, vx]),
                             int(f_now["beaufort"][vy, vx])) * time_h
        total_km += dist_km
        total_h = t
        total_fuel += fuel
        r = float(f_now["hazard_total"][vy, vx])
        risks.append(r)
        max_risk = max(max_risk, r)
        sics.append(float(f_now["sic"][vy, vx]))
        bergs.append(float(f_now["berg_hazard"][vy, vx]))
    risks_a = np.array(risks) if risks else np.array([0.0])
    sics_a = np.array(sics) if sics else np.array([0.0])
    return {
        "distance_km": round(float(total_km), 1),
        "travel_time_h": round(float(total_h), 2),
        "fuel_liters": round(float(total_fuel), 1),
        "mean_hazard": round(float(np.mean(risks_a)), 4),
        "max_hazard": round(float(max_risk), 4),
        "ice_exposure_frac": round(float(np.mean(sics_a >= 0.15)), 4),
        "mean_sic": round(float(np.mean(sics_a)), 4),
        "mean_iceberg_hazard": round(float(np.mean(bergs)) if bergs else 0.0, 4),
        "n_cells": len(path_xy),
    }


def plan_routes(ds: xr.Dataset, start_latlon: Tuple[float, float],
                goal_latlon: Tuple[float, float], profile,
                depart_day_index: int = 0,
                weight_sets: Optional[Dict[str, Dict[str, float]]] = None,
                hazard_weights: Optional[Dict[str, float]] = None,
                icebergs: Optional[List[Dict[str, Any]]] = None,
                spacing_km: Optional[float] = None) -> Dict[str, Any]:
    """Generate Fastest/Safest/Balanced routes (FR-22) with metrics + confidence.

    start/goal_latlon are (lat, lon). Endpoints snap to the nearest navigable
    cell under THIS vessel's limits (same rule as the Phase 5 baseline).
    Raises NoRouteFound (FR-24) when no profile route can reach the goal.
    """
    from backend.uncertainty.engine import compute_combined_confidence
    weight_sets = weight_sets or WEIGHT_PRESETS
    spacing = spacing_km or float(ds.attrs.get("spacing_km", 25.0))
    t_ref, f_ref = _reference_scales(profile, spacing)
    cache = DayFieldsCache(ds, profile, hazard_weights, icebergs, depart_day_index)

    day0 = cache.day(0.0)
    mask = navigable_mask(day0["sic"], landmask=None, max_sic=float(profile.max_sic_limit))
    mask &= ~day0["blocked"]
    lat2d = np.asarray(ds["lat"].values)
    lon2d = np.asarray(ds["lon"].values)
    try:
        start = nearest_valid_cell(lat2d, lon2d, mask, start_latlon[0], start_latlon[1])
        goal = nearest_valid_cell(lat2d, lon2d, mask, goal_latlon[0], goal_latlon[1])
    except ValueError as e:
        # No navigable cell at all (e.g. solid pack over vessel limits):
        # this is an OUT-8 no-route condition, not a crash (FR-24).
        raise NoRouteFound(
            f"no acceptable route found under current constraints: {e}",
            {"blocked_fraction": round(float(np.mean(day0["blocked"])), 4),
             "endpoint": "start_or_goal_unsnappable"}) from e

    try:
        day0_time = str(np.datetime64(ds["time"].values[depart_day_index], "D"))
    except Exception:
        day0_time = str(ds["time"].values[depart_day_index])

    routes: Dict[str, Any] = {}
    for name, w in weight_sets.items():
        search = time_dependent_dijkstra(cache, start, goal, w, t_ref, f_ref)
        metrics = evaluate_path_metrics(cache, search["path_xy"], t_ref, f_ref)
        metrics["weights"] = {k: float(v) for k, v in w.items()}
        metrics["composite_cost"] = round(search["total_cost"], 3)
        metrics["cells_expanded"] = search["cells_expanded"]
        path_latlon = [{"lat": float(lat2d[y, x]), "lon": float(lon2d[y, x])}
                       for y, x in search["path_xy"]]
        routes[name] = {**metrics, "path_xy": search["path_xy"], "path": path_latlon}

    # confidence for the route set: horizon = longest travel time (FR-12/13)
    longest_h = max(r["travel_time_h"] for r in routes.values())
    missing = [] if "uo" in ds else ["glorys12_ocean_current (wind-driven fallback active)"]
    conf = compute_combined_confidence(horizon_h=longest_h, staleness_h=0.0,
                                       missing_inputs=missing,
                                       provenance_sources=["OSI-SAF", "ERA5", "GLORYS12-fallback"])
    return {
        "vessel_id": getattr(profile, "vessel_id", "unknown"),
        "depart_day_index": int(depart_day_index),
        "depart_date": day0_time,
        "start_cell": [int(start[0]), int(start[1])],
        "goal_cell": [int(goal[0]), int(goal[1])],
        "weights": {k: {kk: float(vv) for kk, vv in v.items()} for k, v in weight_sets.items()},
        "reference_scales": {"t_ref_h": round(t_ref, 3), "f_ref_liters": round(f_ref, 1)},
        "routes": routes,
        "confidence": conf.to_dict(),
        "ocean_source_day0": day0["ocean_source"],
        "forcing_imputed_frac_day0": round(float(day0["forcing_imputed_frac"]), 4),
        "days_evaluated": cache.days_built,
    }
