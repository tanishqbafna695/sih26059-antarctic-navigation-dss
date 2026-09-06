"""EnvironmentStore and state accessor interface (Phase 8).

Provides unified access to sea-ice concentration, sea-ice drift, atmospheric weather,
wave fields, and ocean currents across space and time for downstream hazard
computation (Phase 10) and vessel speed/fuel calculation (Phase 11).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import xarray as xr

from .ocean import analyze_ocean
from .weather import analyze_weather, weather_severity_index


@dataclass
class EnvironmentState:
    """Environmental state at a specific spatial coordinate (lon, lat) and timestamp."""

    timestamp: str
    lon: float
    lat: float
    sic: float  # Sea-ice concentration fraction [0.0, 1.0]
    ice_mask: bool  # True if SIC >= threshold (0.15)
    edge_dist_km: float  # Distance to ice edge (km)
    u10_m_s: float
    v10_m_s: float
    wind_speed_knots: float
    wind_direction_deg: float
    beaufort_scale: int
    t2m_celsius: float
    mslp_hpa: float
    swh_m: float
    uo_m_s: float
    vo_m_s: float
    current_speed_knots: float
    ocean_source: str
    weather_severity: float  # [0.0, 1.0]
    ocean_severity: float  # [0.0, 1.0]
    overall_environment_risk: float  # [0.0, 1.0]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "lon": float(self.lon),
            "lat": float(self.lat),
            "sic": float(self.sic),
            "ice_mask": bool(self.ice_mask),
            "edge_dist_km": float(self.edge_dist_km),
            "u10_m_s": float(self.u10_m_s),
            "v10_m_s": float(self.v10_m_s),
            "wind_speed_knots": float(self.wind_speed_knots),
            "wind_direction_deg": float(self.wind_direction_deg),
            "beaufort_scale": int(self.beaufort_scale),
            "t2m_celsius": float(self.t2m_celsius),
            "mslp_hpa": float(self.mslp_hpa),
            "swh_m": float(self.swh_m),
            "uo_m_s": float(self.uo_m_s),
            "vo_m_s": float(self.vo_m_s),
            "current_speed_knots": float(self.current_speed_knots),
            "ocean_source": self.ocean_source,
            "weather_severity": float(self.weather_severity),
            "ocean_severity": float(self.ocean_severity),
            "overall_environment_risk": float(self.overall_environment_risk),
        }


class EnvironmentStore:
    """Accessor store wrapping the merged feature store dataset (features.nc)."""

    def __init__(self, ds: xr.Dataset):
        self.ds = ds
        self.times = pd.to_datetime(ds["time"].values) if "time" in ds.dims else None

    @classmethod
    def from_file(cls, path: Path) -> EnvironmentStore:
        """Load EnvironmentStore from netCDF file path."""
        if not path.exists():
            raise FileNotFoundError(f"Environment feature store file missing: {path}")
        ds = xr.open_dataset(path, engine="h5netcdf")
        return cls(ds)

    def get_state(self, lon: float, lat: float, time: Union[str, pd.Timestamp]) -> EnvironmentState:
        """Query environmental state at a given (lon, lat) coordinate and time."""
        t_target = pd.Timestamp(time)

        # Select nearest time slice
        if "time" in self.ds.dims:
            ds_t = self.ds.sel(time=t_target, method="nearest")
            t_str = str(pd.Timestamp(ds_t["time"].values).isoformat())
        else:
            ds_t = self.ds
            t_str = t_target.isoformat()

        # Select nearest grid cell (handling both curvilinear EPSG:3412 and rectilinear lat/lon)
        if "y" in ds_t.dims and "x" in ds_t.dims:
            # Polar stereographic grid: find nearest cell by minimum distance
            if "lons" in ds_t and "lats" in ds_t:
                lons = ds_t["lons"].values
                lats = ds_t["lats"].values
            elif "longitude" in ds_t and "latitude" in ds_t:
                lons = ds_t["longitude"].values
                lats = ds_t["latitude"].values
            else:
                lons = ds_t.coords["x"].values
                lats = ds_t.coords["y"].values

            if lons.ndim == 1 and lats.ndim == 1:
                mg_lon, mg_lat = np.meshgrid(lons, lats)
            else:
                mg_lon, mg_lat = lons, lats

            dist = (mg_lon - lon) ** 2 + (mg_lat - lat) ** 2
            iy, ix = np.unravel_index(np.argmin(dist), dist.shape)
            cell = ds_t.isel(y=iy, x=ix)
        elif "latitude" in ds_t.dims and "longitude" in ds_t.dims:
            cell = ds_t.sel(latitude=lat, longitude=lon, method="nearest")
        else:
            cell = ds_t

        def _val(var_name: str, default: float = 0.0) -> float:
            if var_name in cell:
                val = float(cell[var_name].values)
                return val if np.isfinite(val) else default
            return default

        sic = float(np.clip(_val("sic", 0.0), 0.0, 1.0))
        ice_mask_bool = bool(cell["ice_mask"].values) if "ice_mask" in cell else (sic >= 0.15)
        edge_dist = _val("edge_dist", 0.0)

        u10 = _val("u10", 0.0)
        v10 = _val("v10", 0.0)
        t2m = _val("t2m", 273.15)
        mslp = _val("mslp", 101325.0)
        swh = _val("swh", 0.0)
        mwp = _val("mwp", 0.0)

        uo = cell["uo"].values if "uo" in cell else None
        vo = cell["vo"].values if "vo" in cell else None
        drift_u = cell["drift_u"].values if "drift_u" in cell else None
        drift_v = cell["drift_v"].values if "drift_v" in cell else None

        uo_float = float(uo) if uo is not None and np.isfinite(uo) else None
        vo_float = float(vo) if vo is not None and np.isfinite(vo) else None
        du_float = float(drift_u) if drift_u is not None and np.isfinite(drift_u) else None
        dv_float = float(drift_v) if drift_v is not None and np.isfinite(drift_v) else None

        w_analysis = analyze_weather(u10, v10, t2m, mslp, swh, mwp)
        o_analysis = analyze_ocean(uo_float, vo_float, u10, v10, du_float, dv_float)

        # Combined environmental risk severity (40% sea-ice, 40% weather, 20% ocean)
        w_sev = w_analysis["weather_severity_index"]
        o_sev = o_analysis["ocean_severity_index"]
        overall_risk = float(min(1.0, max(0.0, 0.40 * sic + 0.40 * w_sev + 0.20 * o_sev)))

        return EnvironmentState(
            timestamp=t_str,
            lon=float(lon),
            lat=float(lat),
            sic=sic,
            ice_mask=ice_mask_bool,
            edge_dist_km=edge_dist,
            u10_m_s=u10,
            v10_m_s=v10,
            wind_speed_knots=w_analysis["wind_speed_knots"],
            wind_direction_deg=w_analysis["wind_direction_deg"],
            beaufort_scale=w_analysis["beaufort_scale"],
            t2m_celsius=w_analysis["temperature_celsius"],
            mslp_hpa=w_analysis["pressure_hpa"],
            swh_m=w_analysis["significant_wave_height_m"],
            uo_m_s=o_analysis["uo_ms"],
            vo_m_s=o_analysis["vo_ms"],
            current_speed_knots=o_analysis["current_speed_knots"],
            ocean_source=o_analysis["current_source"],
            weather_severity=w_sev,
            ocean_severity=o_sev,
            overall_environment_risk=overall_risk,
        )
