"""Unified weather and ocean environment module (Phase 8)."""

from .ocean import analyze_ocean, current_speed_knots, ocean_current_fallback
from .store import EnvironmentState, EnvironmentStore
from .weather import analyze_weather, weather_severity_index

__all__ = [
    "EnvironmentState",
    "EnvironmentStore",
    "analyze_weather",
    "weather_severity_index",
    "analyze_ocean",
    "current_speed_knots",
    "ocean_current_fallback",
]
