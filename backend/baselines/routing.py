"""Shortest-path routing baseline (FR-21).

The baseline route is the geometric shortest path over the navigable-cell
graph (obstacles = land / no-data / beyond ice-capability cells), ignoring
hazard, time and fuel. Later phases (multi-objective routing, Phase 12) must
beat this on modeled hazard exposure for similar time before we claim value.

Implementation: Dijkstra over the common-grid 8-connectivity graph with edge
cost = great-circle km between cell centres. scipy.sparse.csgraph keeps it
fast enough for the ~10^4-10^5 cell domain (NFR-1).
"""
from __future__ import annotations

import numpy as np
import xarray as xr
from scipy import sparse
from scipy.sparse.csgraph import dijkstra

from .metrics import haversine_km


def navigable_mask(sic: np.ndarray, landmask: np.ndarray | None = None,
                   max_sic: float = 0.8) -> np.ndarray:
    """Cells a vessel may transit: valid SIC, not land, below max concentration.

    Hard constraints (FR-17 / Phase 0 §7.3): no-data and land are rejected;
    SIC above max_sic is treated as an obstacle for the baseline. max_sic=0.8
    is the default "not fast-ice" rule; vessel-specific limits arrive Phase 11.
    """
    ok = np.isfinite(np.asarray(sic, dtype=float))
    if landmask is not None:
        ok &= ~np.asarray(landmask, dtype=bool)
    if max_sic is not None:
        ok &= np.asarray(sic, dtype=float) <= max_sic
    return ok


def nearest_valid_cell(lat2d: np.ndarray, lon2d: np.ndarray, mask: np.ndarray,
                       target_lat: float, target_lon: float) -> tuple[int, int]:
    """Index (y, x) of the nearest navigable cell to a target lon/lat."""
    d = np.abs(lat2d - target_lat) + np.abs(lon2d - target_lon)
    d = np.where(mask, d, np.inf)
    if not np.isfinite(d).any():
        raise ValueError(f"no navigable cell near ({target_lat}, {target_lon})")
    y, x = np.unravel_index(np.nanargmin(d), d.shape)
    return int(y), int(x)


def build_graph(lat2d: np.ndarray, lon2d: np.ndarray, mask: np.ndarray,
                diagonal: bool = True) -> tuple[sparse.csr_matrix, dict]:
    """Sparse adjacency (edge weight = km) over navigable cells."""
    ny, nx = mask.shape
    n = ny * nx
    idx = np.full((ny, nx), -1, dtype=np.int64)
    idx[mask] = np.arange(mask.sum())
    n_ok = mask.sum()

    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    if diagonal:
        moves += [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    rows, cols, weights = [], [], []
    for y in range(ny):
        for x in range(nx):
            if not mask[y, x]:
                continue
            i = idx[y, x]
            for dy, dx in moves:
                nyy, nxx = y + dy, x + dx
                if 0 <= nyy < ny and 0 <= nxx < nx and mask[nyy, nxx]:
                    w = haversine_km(lon2d[y, x], lat2d[y, x],
                                     lon2d[nyy, nxx], lat2d[nyy, nxx])
                    rows.append(i)
                    cols.append(idx[nyy, nxx])
                    weights.append(w)
    g = sparse.csr_matrix((weights, (rows, cols)), shape=(n_ok, n_ok))
    # nodes: (y, x) -> flattened index for the caller
    node_of = {(int(y), int(x)): int(idx[y, x]) for y in range(ny) for x in range(nx)
               if mask[y, x]}
    return g, node_of


def shortest_path(lat2d: np.ndarray, lon2d: np.ndarray, mask: np.ndarray,
                  start: tuple[int, int], goal: tuple[int, int],
                  diagonal: bool = True) -> dict:
    """Dijkstra shortest path between two (y, x) cells. Returns route dict."""
    g, node_of = build_graph(lat2d, lon2d, mask, diagonal=diagonal)
    s, t = node_of[start], node_of[goal]
    dist, pred, _sources = dijkstra(g, directed=False, indices=s,
                                    return_predecessors=True, min_only=True)
    if not np.isfinite(dist[t]):
        return {"found": False, "reason": "no navigable path between endpoints",
                "distance_km": float("inf"), "path": [], "path_xy": []}

    # reconstruct path (pred gives previous node toward source)
    path_nodes = [t]
    while path_nodes[-1] != s:
        prev = int(pred[path_nodes[-1]])
        if prev < 0:  # safety: no predecessor (should not happen when reachable)
            break
        path_nodes.append(prev)
    path_nodes.reverse()
    # map node id -> (y, x)
    node_to_cell = {v: k for k, v in node_of.items()}
    path_xy = [node_to_cell[n] for n in path_nodes]
    path_latlon = [{"lat": float(lat2d[y, x]), "lon": float(lon2d[y, x])}
                   for y, x in path_xy]
    return {"found": True, "distance_km": float(dist[t]),
            "path": path_latlon, "path_xy": path_xy, "n_cells": len(path_xy),
            "mean_lat": float(np.mean([p["lat"] for p in path_latlon])),
            "mean_lon": float(np.mean([p["lon"] for p in path_latlon]))}


def baseline_route_from_store(store: xr.Dataset, day_index: int,
                              start_latlon: tuple[float, float],
                              goal_latlon: tuple[float, float],
                              max_sic: float = 0.8) -> dict:
    """Shortest-path baseline between two lon/lat points on a given day."""
    sic = store["sic"].values[day_index]
    land = store["landmask"].values if "landmask" in store else None
    lat2d = store["lat"].values
    lon2d = store["lon"].values
    mask = navigable_mask(sic, land, max_sic=max_sic)
    start = nearest_valid_cell(lat2d, lon2d, mask, *start_latlon)
    goal = nearest_valid_cell(lat2d, lon2d, mask, *goal_latlon)
    return shortest_path(lat2d, lon2d, mask, start, goal)
