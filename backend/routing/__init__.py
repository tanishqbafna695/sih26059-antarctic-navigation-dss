"""Phase 12 — Multi-objective route optimization (FR-22, FR-23, FR-24).

Time-aware Dijkstra over the vessel-specific polar hazard field: edge costs
combine modeled risk, transit time and fuel with configurable weights
(Cost = a*Risk + b*Time + g*Fuel). Blocked cells are hard obstacles; an
unreachable goal returns a no-route statement (OUT-8), never a fake route.
"""

from .costs import WEIGHT_PRESETS, DayFieldsCache, build_day_fields
from .optimizer import NoRouteFound, plan_routes

__all__ = [
    "WEIGHT_PRESETS",
    "DayFieldsCache",
    "build_day_fields",
    "NoRouteFound",
    "plan_routes",
]
