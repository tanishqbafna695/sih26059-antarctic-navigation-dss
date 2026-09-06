"""FastAPI application for the Antarctic Navigation DSS (Phase 18, FR-33–FR-36).

Endpoints:
  GET  /api/v1/health           — system health + data status
  GET  /api/v1/vessels          — registered vessel profiles (FR-19)
  GET  /api/v1/corridors        — available demo corridors
  POST /api/v1/plan             — full pipeline: corridor → routes → recommendation → explanation
  POST /api/v1/reroute          — mid-voyage re-route decision (FR-30/31)
  GET  /api/v1/validation       — FR-36 baseline-vs-model metrics
  GET  /api/v1/events/environment — FR-35 SSE environment stream (polling fallback)

DESIGN RULES (Phase 0):
- Every response traces to recorded numbers or the feature store; nothing fabricated.
- No-route is a legitimate API response (FR-24/OUT-8), never a 500.
- Confidence is a qualifier, not per-route precision (Phase 13 discipline).
- Demo mode (FR-34): all endpoints work offline against the bundled feature store.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import xarray as xr
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from backend.api.schemas import (
    CorridorInfo,
    HealthResponse,
    IcebergFix,
    LatLon,
    PlanRequest,
    RerouteRequest,
    RerouteResult,
    RouteSet,
    RouteWithGeometry,
    ValidationResponse,
    VesselInfo,
)
from backend.baselines.routing import navigable_mask, nearest_valid_cell
from backend.environment.store import EnvironmentStore
from backend.rerouting.reroute import RerouteThresholds, reroute
from backend.routing.costs import WEIGHT_PRESETS
from backend.routing.optimizer import NoRouteFound, arrival_times, evaluate_path_metrics, plan_routes
from backend.tradeoff.comparison import build_comparison
from backend.tradeoff.recommend import PRIORITY_PROFILES, recommend
from backend.vessel.profile import PRESET_PROFILES, VesselRegistry

ROOT = Path(__file__).resolve().parents[2]
STORE_PATH = ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"
DATA_ROOT = ROOT / "data"

# ── Demo corridors (FR-34 deterministic offline mode) ──────────────────────
CORRIDORS: List[Dict[str, Any]] = [
    {
        "id": "bharati_maitri",
        "name": "Bharati to Maitri",
        "origin": {"lat": -69.41, "lon": 76.19},
        "destination": {"lat": -70.77, "lon": 11.73},
        "description": "Primary Antarctic corridor between Indian research stations (Mishra et al. 2021 benchmark).",
    },
]


def _load_feature_store() -> xr.Dataset:
    """Open the feature store, raising a clear error if missing."""
    if not STORE_PATH.exists():
        raise FileNotFoundError(
            f"Feature store not found at {STORE_PATH}. "
            "Run: python scripts/data_fetch/fetch_all.py --synthetic"
        )
    return xr.open_dataset(str(STORE_PATH), engine="h5netcdf")


def _load_recorded_report(name: str) -> Optional[Dict[str, Any]]:
    """Load a recorded JSON report from data/<name>/latest.json."""
    p = DATA_ROOT / name / "latest.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def _snap_to_grid(lat2d: np.ndarray, lon2d: np.ndarray, mask: np.ndarray,
                  lat: float, lon: float) -> Dict[str, Any]:
    """Snap a lat/lon to the nearest navigable grid cell."""
    try:
        y, x = nearest_valid_cell(lat2d, lon2d, mask, lat, lon)
        return {"y": int(y), "x": int(x),
                "lat": round(float(lat2d[y, x]), 4),
                "lon": round(float(lon2d[y, x]), 4)}
    except ValueError:
        return {"y": -1, "x": -1, "lat": lat, "lon": lon, "error": "no navigable cell"}


# ── App factory ─────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Antarctic Ship-Route Advisor API",
        description=(
            "SIH26059 — AI-Enabled Antarctic Sea-Ice, Iceberg Trajectory & "
            "Navigation Decision Support System. REST/JSON API exposing "
            "scenario → forecast → hazard → routes → recommendation → re-route."
        ),
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Singletons (loaded once at startup) ────────────────────────────────
    _ds: Optional[xr.Dataset] = None
    _reg = VesselRegistry()

    def _get_ds() -> xr.Dataset:
        nonlocal _ds
        if _ds is None:
            _ds = _load_feature_store()
        return _ds

    # ── GET /health ────────────────────────────────────────────────────────
    @app.get("/api/v1/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        ds = _get_ds()
        return HealthResponse(
            feature_store={
                "path": str(STORE_PATH),
                "n_days": int(ds.sizes["time"]),
                "shape_yx": (int(ds.sizes["y"]), int(ds.sizes["x"])),
                "variables": list(ds.data_vars),
            },
            data_sources=["OSI SAF SIC CDR (CC-BY-4.0)", "ERA5 (Copernicus licence)",
                           "OSI SAF drift (CC-BY-4.0)"],
            model_versions={
                "sea_ice_forecast": "seasonal-climatology v1 (Phase 6)",
                "iceberg_drift": "physics-guided empirical (Phase 7)",
                "hazard_field": "multi-component weighted (Phase 10)",
                "route_optimizer": "time-dependent Dijkstra (Phase 12)",
            },
        )

    # ── GET /vessels ───────────────────────────────────────────────────────
    @app.get("/api/v1/vessels", response_model=List[VesselInfo])
    def list_vessels() -> List[VesselInfo]:
        return [VesselInfo(**p.to_dict()) for p in _reg.list_profiles()]

    # ── GET /corridors ─────────────────────────────────────────────────────
    @app.get("/api/v1/corridors", response_model=List[CorridorInfo])
    def list_corridors() -> List[CorridorInfo]:
        return [CorridorInfo(**c) for c in CORRIDORS]

    # ── POST /plan ─────────────────────────────────────────────────────────
    @app.post("/api/v1/plan", response_model=RouteSet)
    def plan_voyage(req: PlanRequest) -> RouteSet:
        ds = _get_ds()

        # Resolve vessel profile
        try:
            profile = _reg.get_profile(req.vessel_id)
        except KeyError as e:
            raise HTTPException(status_code=422, detail=str(e))

        # Apply custom overrides (FR-19)
        if req.custom_vessel_overrides:
            profile = _reg.create_custom_profile(
                req.vessel_id, req.custom_vessel_overrides)

        # Snap endpoints to grid
        lat2d = np.asarray(ds["lat"].values)
        lon2d = np.asarray(ds["lon"].values)
        n_days = int(ds.sizes["time"])
        di = max(0, min(n_days - 1, req.depart_day_index))

        # Use day-0 mask for snapping (same as optimizer)
        ds_day0 = ds.isel(time=di)
        sic0 = np.clip(np.asarray(ds_day0["sic"].values, dtype=float), 0, 1)
        mask = navigable_mask(sic0, landmask=None, max_sic=profile.max_sic_limit)

        origin_snapped = _snap_to_grid(lat2d, lon2d, mask, req.origin.lat, req.origin.lon)
        dest_snapped = _snap_to_grid(lat2d, lon2d, mask, req.destination.lat, req.destination.lon)

        # Convert iceberg fixes to the dict format the backend expects
        berg_dicts = [
            {"lon": b.lon, "lat": b.lat,
             "v_east_kmh": b.v_east_kmh, "v_north_kmh": b.v_north_kmh,
             "obs_staleness_h": b.obs_staleness_h, "label": b.label}
            for b in req.icebergs
        ]

        try:
            result = plan_routes(
                ds,
                start_latlon=(req.origin.lat, req.origin.lon),
                goal_latlon=(req.destination.lat, req.destination.lon),
                profile=profile,
                depart_day_index=di,
                icebergs=berg_dicts,
            )
        except NoRouteFound as e:
            # FR-24: no-route is a legitimate response, not a 500
            comp = {"routes_available": False, "reason": str(e),
                    "vessel_id": profile.vessel_id,
                    "confidence": {"overall_confidence": 0.0,
                                   "status_label": "NO_ROUTE"}}
            rec = recommend(comp, req.priority)
            return _no_route_response(
                profile, di, origin_snapped, dest_snapped, e, comp, rec)

        # Build comparison + recommendation
        comp = build_comparison(result)
        rec = recommend(comp, req.priority)

        # Explanation
        from backend.explanation import explain_recommendation
        vessel_info = {
            "name": profile.name, "ice_class": profile.ice_class,
            "max_sic_limit": float(profile.max_sic_limit),
        }
        explanation = explain_recommendation(comp.get("rows", []), rec, vessel_info)

        # Build route geometry
        routes_out: Dict[str, RouteWithGeometry] = {}
        for name, r in result.get("routes", {}).items():
            path_latlon = [{"lat": p["lat"], "lon": p["lon"]}
                           for p in r.get("path", [])]
            routes_out[name] = RouteWithGeometry(
                route=name,
                travel_time_h=r["travel_time_h"],
                fuel_liters=r["fuel_liters"],
                mean_hazard=r["mean_hazard"],
                max_hazard=r["max_hazard"],
                ice_exposure_frac=r["ice_exposure_frac"],
                distance_km=r["distance_km"],
                n_cells=r.get("n_cells", len(path_latlon)),
                path_latlon=path_latlon,
            )

        try:
            depart_date = str(np.datetime64(ds["time"].values[di], "D"))
        except Exception:
            depart_date = str(ds["time"].values[di])

        return RouteSet(
            vessel_id=profile.vessel_id,
            depart_date=depart_date,
            depart_day_index=di,
            origin_snapped=origin_snapped,
            destination_snapped=dest_snapped,
            routes=routes_out,
            recommendation=rec,
            explanation=explanation,
            confidence=result.get("confidence", {}),
            ocean_source=result.get("ocean_source_day0", "unknown"),
            forcing_imputed_frac=result.get("forcing_imputed_frac_day0", 0.0),
        )

    # ── POST /reroute ──────────────────────────────────────────────────────
    @app.post("/api/v1/reroute", response_model=RerouteResult)
    def re_route(req: RerouteRequest) -> RerouteResult:
        ds = _get_ds()

        # Resolve vessel
        try:
            profile = _reg.get_profile(req.old_plan.vessel_id)
        except KeyError as e:
            raise HTTPException(status_code=422, detail=str(e))
        if req.old_plan.custom_vessel_overrides:
            profile = _reg.create_custom_profile(
                req.old_plan.vessel_id, req.old_plan.custom_vessel_overrides)

        # Get old plan's path via the full chain (we need path_xy)
        old_result = plan_routes(
            ds,
            start_latlon=(req.old_plan.origin.lat, req.old_plan.origin.lon),
            goal_latlon=(req.old_plan.destination.lat, req.old_plan.destination.lon),
            profile=profile,
            depart_day_index=req.old_plan.depart_day_index,
            icebergs=[{"lon": b.lon, "lat": b.lat,
                       "v_east_kmh": b.v_east_kmh, "v_north_kmh": b.v_north_kmh,
                       "obs_staleness_h": b.obs_staleness_h, "label": b.label}
                      for b in req.old_plan.icebergs],
        )

        old_route = old_result["routes"].get(req.old_winner_route)
        if old_route is None:
            raise HTTPException(
                status_code=422,
                detail=f"old_winner_route '{req.old_winner_route}' not found in the plan")

        old_path = [tuple(p) for p in old_route["path_xy"]]
        new_day = req.new_depart_day_index if req.new_depart_day_index is not None else req.old_plan.depart_day_index
        new_bergs = [{"lon": b.lon, "lat": b.lat,
                      "v_east_kmh": b.v_east_kmh, "v_north_kmh": b.v_north_kmh,
                      "obs_staleness_h": b.obs_staleness_h, "label": b.label}
                     for b in req.new_icebergs]
        old_bergs = [{"lon": b.lon, "lat": b.lat,
                      "v_east_kmh": b.v_east_kmh, "v_north_kmh": b.v_north_kmh,
                      "obs_staleness_h": b.obs_staleness_h, "label": b.label}
                     for b in req.old_plan.icebergs]

        result = reroute(
            ds, profile, old_path, req.old_winner_route,
            req.old_plan.depart_day_index, old_bergs,
            req.elapsed_hours, new_day, new_bergs,
            priority=req.old_priority,
            staleness_h=req.staleness_hours,
            frozen_day_index=req.frozen_day_index,
        )

        # Convert path_xy to latlon in new_routes
        new_routes_out: Optional[Dict[str, RouteWithGeometry]] = None
        if result.get("new_routes"):
            new_routes_out = {}
            for name, r in result["new_routes"].items():
                path_xy = r.get("path_xy", [])
                lat2d = np.asarray(ds["lat"].values)
                lon2d = np.asarray(ds["lon"].values)
                path_latlon = [{"lat": round(float(lat2d[y, x]), 4),
                               "lon": round(float(lon2d[y, x]), 4)}
                              for y, x in path_xy]
                new_routes_out[name] = RouteWithGeometry(
                    route=name,
                    travel_time_h=r["travel_time_h"],
                    fuel_liters=r["fuel_liters"],
                    mean_hazard=r["mean_hazard"],
                    max_hazard=r["max_hazard"],
                    ice_exposure_frac=r["ice_exposure_frac"],
                    distance_km=r.get("distance_km", 0),
                    n_cells=r.get("n_cells", len(path_xy)),
                    path_latlon=path_latlon,
                )

        return RerouteResult(
            outcome=result["outcome"],
            current_cell=result.get("current_cell", []),
            elapsed_h=result.get("elapsed_h", req.elapsed_hours),
            changes=result.get("changes", {}),
            old_remaining_if_staying=result.get("old_remaining_if_staying"),
            new_routes=new_routes_out,
            new_recommendation=result.get("new_recommendation"),
            change_explanation=result.get("change_explanation"),
            new_explanation=result.get("new_explanation"),
            confidence=result.get("confidence", {}),
        )

    # ── GET /validation (FR-36) ────────────────────────────────────────────
    @app.get("/api/v1/validation", response_model=ValidationResponse)
    def validation_metrics() -> ValidationResponse:
        """Return baseline-vs-model metrics from recorded reports."""
        sea_ice = _load_recorded_report("forecast")
        iceberg = _load_recorded_report("iceberg")
        routing = _load_recorded_report("routing")

        def _extract(d: Optional[Dict], *keys: str) -> Dict[str, Any]:
            if d is None:
                return {"status": "report not found on disk"}
            out = {}
            for k in keys:
                if k in d:
                    out[k] = d[k]
            return out or {"status": "keys not present", "available_keys": list(d.keys())}

        return ValidationResponse(
            sea_ice=_extract(sea_ice, "ridges", "seasonal_climatology", "persistence"),
            iceberg=_extract(iceberg, "constant_velocity_baseline", "physics_drift_model"),
            routing=_extract(routing, "vessels", "baseline_shortest_path"),
            data_window="Dec 2019 - Mar 2020 (Bharati-Maitri corridor)",
        )

    # ── GET /events/environment (FR-35 SSE) ────────────────────────────────
    @app.get("/api/v1/events/environment")
    def environment_stream(
        day: int = Query(0, ge=0, description="Starting day index"),
        interval_sec: float = Query(2.0, ge=0.5, le=30.0,
                                    description="Seconds between events"),
    ):
        """FR-35: Server-sent events pushing environment snapshots for demo replay.

        Each event carries a JSON payload with the day index, a sample of the
        sea-ice concentration and weather fields, and the confidence level.
        The client can drive a time-slider from this stream.
        """
        ds = _get_ds()
        n_days = int(ds.sizes["time"])

        def _generate():
            for i in range(day, n_days):
                ds_i = ds.isel(time=i)
                try:
                    dt = str(np.datetime64(ds["time"].values[i], "D"))
                except Exception:
                    dt = str(ds["time"].values[i])
                sic = np.asarray(ds_i["sic"].values, dtype=float)
                valid_frac = float(np.mean(np.isfinite(sic) & (sic > 0)))
                payload = {
                    "day_index": i,
                    "date": dt,
                    "ice_covered_frac": round(valid_frac, 4),
                    "n_valid_cells": int(np.sum(np.isfinite(sic))),
                    "n_total_cells": int(sic.size),
                }
                yield {"event": "environment", "data": json.dumps(payload)}
                time.sleep(interval_sec)

        return EventSourceResponse(_generate())

    return app


# ── Helpers ─────────────────────────────────────────────────────────────────

def _no_route_response(profile, di, origin_snapped, dest_snapped, exc, comp, rec):
    """Build a RouteSet for the no-route case (FR-24)."""
    return RouteSet(
        vessel_id=profile.vessel_id,
        depart_date="unknown",
        depart_day_index=di,
        origin_snapped=origin_snapped,
        destination_snapped=dest_snapped,
        routes={},
        recommendation=rec,
        explanation={
            "explained": False,
            "reason": str(exc),
            "headline": f"No acceptable route: {exc}",
            "strengths": [],
            "prices": [],
            "vessel_statement": "",
            "confidence_note": "",
            "caveats": [],
            "text": f"No acceptable route: {exc}",
        },
        confidence=comp.get("confidence", {}),
        ocean_source="unknown",
        forcing_imputed_frac=0.0,
    )
