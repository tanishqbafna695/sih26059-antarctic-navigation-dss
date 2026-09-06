"""Pydantic request/response schemas for the Antarctic Navigation DSS API.

All fields are documented, defaults chosen for the Bharati-Maitri demo corridor,
and validators enforce hard physical constraints at the API boundary so the
backend never sees illegal input (defense-in-depth; the internal modules have
their own checks per FR-17/24).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Shared helpers ──────────────────────────────────────────────────────────

class LatLon(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lon: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")


class IcebergFix(BaseModel):
    lon: float = Field(..., description="Current longitude of the iceberg fix")
    lat: float = Field(..., description="Current latitude of the iceberg fix")
    v_east_kmh: float = Field(0.0, description="Eastward velocity (km/h) if known")
    v_north_kmh: float = Field(0.0, description="Northward velocity (km/h) if known")
    obs_staleness_h: float = Field(0.0, ge=0, description="Hours since last observation")
    label: str = Field("observed", description="Source label (observed / ASSUMED)")


class RouteMetrics(BaseModel):
    route: str
    travel_time_h: float
    fuel_liters: float
    mean_hazard: float
    max_hazard: float
    ice_exposure_frac: float
    distance_km: float
    n_cells: int = 0


class RouteWithGeometry(RouteMetrics):
    path_latlon: List[Dict[str, float]] = Field(
        default_factory=list,
        description="Ordered [{lat, lon}] waypoints of the route")


# ── Request schemas ─────────────────────────────────────────────────────────

class PlanRequest(BaseModel):
    """POST /api/v1/plan — full planning pipeline (FR-33)."""
    origin: LatLon = Field(
        ...,
        description="Departure position (lat/lon). Snapped to nearest navigable grid cell.")
    destination: LatLon = Field(
        ...,
        description="Destination position (lat/lon). Snapped to nearest navigable grid cell.")
    vessel_id: str = Field(
        "polar_class_pc7",
        description="Preset vessel profile ID (open_water_rv / polar_class_pc7 / polar_class_pc1)")
    depart_day_index: int = Field(
        45, ge=0,
        description="Dataset day index for departure (0 = 2019-12-01, 45 = 2020-01-15)")
    priority: str = Field(
        "balanced",
        description="Navigator priority profile (balanced / safety_first / time_first / fuel_saver)")
    icebergs: List[IcebergFix] = Field(
        default_factory=list,
        description="Known iceberg positions (real or labeled ASSUMED)")
    custom_vessel_overrides: Optional[Dict[str, Any]] = Field(
        None,
        description="FR-19 custom vessel parameter overrides applied on top of the preset")


class RerouteRequest(BaseModel):
    """POST /api/v1/reroute — mid-voyage re-route (FR-30/31)."""
    old_plan: PlanRequest = Field(..., description="Original plan request")
    old_priority: str = Field("balanced", description="Priority used for the original plan")
    old_winner_route: str = Field("safest", description="Name of the previously advised route")
    elapsed_hours: float = Field(..., ge=0, description="Hours already sailed along the old route")
    new_icebergs: List[IcebergFix] = Field(
        default_factory=list,
        description="Updated iceberg positions (may differ from the original plan)")
    new_depart_day_index: Optional[int] = Field(
        None,
        description="New departure day index for re-evaluation (None = same as original)")
    staleness_hours: float = Field(0.0, ge=0, description="Hours since last fresh observation")
    frozen_day_index: Optional[int] = Field(
        None,
        description="FR-32 SC-4: cap data at this day index to model a sensor outage")


# ── Response schemas ────────────────────────────────────────────────────────

class RouteSet(BaseModel):
    vessel_id: str
    depart_date: str
    depart_day_index: int
    origin_snapped: Dict[str, Any] = Field(description="Snapped origin cell coordinates")
    destination_snapped: Dict[str, Any] = Field(description="Snapped destination cell coordinates")
    routes: Dict[str, RouteWithGeometry]
    recommendation: Dict[str, Any] = Field(description="Priority recommendation (Phase 13)")
    explanation: Dict[str, Any] = Field(description="Template explanation (Phase 14)")
    confidence: Dict[str, Any] = Field(description="Unified confidence report (Phase 9)")
    ocean_source: str
    forcing_imputed_frac: float
    baseline_sic_forecast: Optional[Dict[str, Any]] = Field(
        None,
        description="FR-5/6 SIC forecast if requested")


class RerouteResult(BaseModel):
    outcome: str = Field(description="RE-ROUTE / ADJUSTED / HOLDS / COMPLETE / NO_ROUTE")
    current_cell: List[int]
    elapsed_h: float
    changes: Dict[str, Any]
    old_remaining_if_staying: Optional[Dict[str, Any]] = None
    new_routes: Optional[Dict[str, RouteWithGeometry]] = None
    new_recommendation: Optional[Dict[str, Any]] = None
    change_explanation: Optional[Dict[str, Any]] = None
    new_explanation: Optional[Dict[str, Any]] = None
    confidence: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    feature_store: Dict[str, Any]
    data_sources: List[str]
    model_versions: Dict[str, str]


class VesselInfo(BaseModel):
    vessel_id: str
    name: str
    ice_class: str
    max_sic_limit: float
    max_speed_kts: float
    cruise_speed_kts: float
    base_fuel_rate_lph: float
    draft_m: float
    beam_m: float
    max_swh_limit: float
    max_wind_limit: float


class CorridorInfo(BaseModel):
    id: str
    name: str
    origin: LatLon
    destination: LatLon
    description: str


class ValidationResponse(BaseModel):
    """FR-36: baseline vs model validation metrics."""
    sea_ice: Dict[str, Any]
    iceberg: Dict[str, Any]
    routing: Dict[str, Any]
    data_window: str
