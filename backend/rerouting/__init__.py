"""Phase 15 — Dynamic Re-Routing (FR-30, FR-31, FR-32).

Mid-voyage environment updates (new day's observations, fresh iceberg
fixes) re-run the full chain from the vessel's current position:
detect changes against configurable thresholds, recompute the three routes
under new conditions, compare staying-the-course versus the new advice, and
emit an OUT-6 re-route notice with a Phase 14 change explanation.
"""

from .reroute import RerouteThresholds, detect_changes, reroute

__all__ = [
    "RerouteThresholds",
    "detect_changes",
    "reroute",
]
