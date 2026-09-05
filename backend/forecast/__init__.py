"""Forecast models (Phases 6+).

Phase 6: sea-ice concentration forecast (FR-5, FR-7). Progression per Phase 0
§41: persistence baseline (Phase 5) -> simple classical ML here -> more
advanced models only if the simple one is insufficient.
"""

from . import sea_ice

__all__ = ["sea_ice"]
