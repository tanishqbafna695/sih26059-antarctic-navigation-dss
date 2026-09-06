"""Vessel performance and fuel consumption module (FR-18, FR-19, FR-20, Phase 11)."""

from .performance import calculate_effective_speed, calculate_fuel_rate, evaluate_leg_performance
from .profile import PRESET_PROFILES, VesselProfile, VesselRegistry

__all__ = [
    "VesselProfile",
    "VesselRegistry",
    "PRESET_PROFILES",
    "calculate_effective_speed",
    "calculate_fuel_rate",
    "evaluate_leg_performance",
]
