"""Vessel Profile Registry and Data Model (FR-18, FR-19, Phase 11).

Defines VesselProfile parameters (ice capability, cruising speed, fuel burn rates,
draft, operating limits) and VesselRegistry supporting presets and custom overrides.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class VesselProfile:
    """Vessel specification and operational limits profile."""

    vessel_id: str
    name: str
    ice_class: str  # e.g. "Open Water", "PC7", "PC1"
    max_sic_limit: float  # Maximum allowable SIC fraction [0.0, 1.0]
    max_speed_kts: float  # Maximum open water speed in knots
    cruise_speed_kts: float  # Economical cruising speed in open water in knots
    base_fuel_rate_lph: float  # Base fuel burn rate at cruising speed (Liters/hour)
    max_fuel_rate_lph: float  # Maximum fuel burn rate at full power / heavy ice (Liters/hour)
    draft_m: float  # Vessel draft in meters
    beam_m: float  # Vessel beam width in meters
    max_swh_limit: float = 4.0  # Maximum operating significant wave height (meters)
    max_wind_limit: float = 34.0  # Maximum operating wind speed (knots)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VesselProfile:
        return cls(**data)


PRESET_PROFILES: Dict[str, VesselProfile] = {
    "open_water_rv": VesselProfile(
        vessel_id="open_water_rv",
        name="Open Water Research Vessel",
        ice_class="Open Water",
        max_sic_limit=0.15,
        max_speed_kts=16.0,
        cruise_speed_kts=14.0,
        base_fuel_rate_lph=400.0,
        max_fuel_rate_lph=800.0,
        draft_m=6.0,
        beam_m=18.0,
        max_swh_limit=2.5,
        max_wind_limit=25.0,
        notes="Non-ice-strengthened polar research ship; avoids ice pack completely.",
    ),
    "polar_class_pc7": VesselProfile(
        vessel_id="polar_class_pc7",
        name="Polar Class PC7 Vessel",
        ice_class="PC7",
        max_sic_limit=0.60,
        max_speed_kts=14.0,
        cruise_speed_kts=12.0,
        base_fuel_rate_lph=550.0,
        max_fuel_rate_lph=1100.0,
        draft_m=7.5,
        beam_m=22.0,
        max_swh_limit=4.0,
        max_wind_limit=34.0,
        notes="Medium ice-strengthened vessel capable of thin first-year ice navigation.",
    ),
    "polar_class_pc1": VesselProfile(
        vessel_id="polar_class_pc1",
        name="Heavy Polar Icebreaker PC1",
        ice_class="PC1",
        max_sic_limit=1.00,
        max_speed_kts=18.0,
        cruise_speed_kts=15.0,
        base_fuel_rate_lph=900.0,
        max_fuel_rate_lph=1800.0,
        draft_m=9.0,
        beam_m=28.0,
        max_swh_limit=6.0,
        max_wind_limit=50.0,
        notes="Heavy polar icebreaker capable of year-round operation in all polar waters.",
    ),
}


class VesselRegistry:
    """Registry managing default presets and custom user vessel profiles."""

    def __init__(self) -> None:
        self._profiles: Dict[str, VesselProfile] = {k: v for k, v in PRESET_PROFILES.items()}

    def get_profile(self, profile_id: str) -> VesselProfile:
        """Get vessel profile by ID or name (raises KeyError if not found)."""
        if profile_id in self._profiles:
            return self._profiles[profile_id]

        # Case-insensitive lookup by name
        for p in self._profiles.values():
            if p.name.lower() == profile_id.lower():
                return p

        available = sorted(self._profiles.keys())
        raise KeyError(f"Unknown vessel profile {profile_id!r}. Available: {available}")

    def list_profiles(self) -> List[VesselProfile]:
        """Return list of all registered vessel profiles."""
        return list(self._profiles.values())

    def register_profile(self, profile: VesselProfile) -> None:
        """Register a new or updated vessel profile."""
        self._profiles[profile.vessel_id] = profile

    def create_custom_profile(self, base_preset_id: str, overrides: Dict[str, Any]) -> VesselProfile:
        """Create a custom vessel profile derived from a base preset with parameter overrides (FR-19)."""
        base = self.get_profile(base_preset_id)
        data = base.to_dict()
        data.update(overrides)

        if "vessel_id" not in overrides:
            data["vessel_id"] = f"{base.vessel_id}_custom"
        if "name" not in overrides:
            data["name"] = f"{base.name} (Custom)"

        custom = VesselProfile.from_dict(data)
        self.register_profile(custom)
        return custom
