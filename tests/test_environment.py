"""Unit tests for Phase 8 weather and ocean environment module."""

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from backend.environment import (
    EnvironmentState,
    EnvironmentStore,
    analyze_ocean,
    analyze_weather,
    current_speed_knots,
    ocean_current_fallback,
    weather_severity_index,
)
from backend.environment.ocean import estimate_wind_driven_surface_current
from backend.environment.weather import beaufort_scale, wind_direction_deg, wind_speed_m_s


def test_wind_speed_and_knots_conversion():
    ws_ms = wind_speed_m_s(3.0, 4.0)
    assert ws_ms == pytest.approx(5.0)

    ws_kts = current_speed_knots(3.0, 4.0)
    assert ws_kts == pytest.approx(5.0 * 1.94384)


def test_wind_direction_meteorological():
    # Wind from North (u=0, v=-5) -> direction 0/360 deg
    dir_n = wind_direction_deg(0.0, -5.0)
    assert dir_n == pytest.approx(0.0) or dir_n == pytest.approx(360.0)

    # Wind from West (u=5, v=0) -> direction 270 deg
    dir_w = wind_direction_deg(5.0, 0.0)
    assert dir_w == pytest.approx(270.0)


def test_beaufort_scale_mapping():
    assert beaufort_scale(0.5) == 0
    assert beaufort_scale(15.0) == 4
    assert beaufort_scale(30.0) == 7  # High wind / Near gale
    assert beaufort_scale(65.0) == 12  # Hurricane / Severe storm


def test_weather_severity_index_bounds():
    # Low wind, mild temp -> low severity
    sev_low = weather_severity_index(u10=2.0, v10=2.0, t2m_k=275.0, swh_m=0.5)
    assert 0.0 <= sev_low <= 0.3

    # High gale wind, cold temp, high waves -> high severity
    sev_high = weather_severity_index(u10=20.0, v10=15.0, t2m_k=255.0, swh_m=5.0)
    assert 0.7 <= sev_high <= 1.0


def test_ocean_current_fallback_chain():
    # 1. GLORYS12 available
    uo, vo, src = ocean_current_fallback(0.3, 0.1, u10_m_s=10.0, v10_m_s=0.0)
    assert uo == pytest.approx(0.3)
    assert src == "glorys12"

    # 2. GLORYS12 missing (NaN), Sea-ice drift available
    uo, vo, src = ocean_current_fallback(np.nan, np.nan, u10_m_s=10.0, v10_m_s=0.0, drift_u=0.15, drift_v=0.05)
    assert uo == pytest.approx(0.15)
    assert src == "sea_ice_drift"

    # 3. Both GLORYS12 and Sea-ice drift missing -> Wind-driven fallback
    uo, vo, src = ocean_current_fallback(None, None, u10_m_s=10.0, v10_m_s=0.0)
    assert src == "wind_driven_estimate"
    assert uo != 0.0  # Wind-driven estimate computed


def test_environment_store_point_query(tmp_path):
    # Build minimal synthetic dataset
    times = pd.date_range("2019-12-01", "2019-12-05", freq="D")
    lats = np.linspace(-70.0, -65.0, 5)
    lons = np.linspace(10.0, 20.0, 5)
    mg_lon, mg_lat = np.meshgrid(lons, lats)

    ds = xr.Dataset(
        {
            "sic": (("time", "y", "x"), np.full((5, 5, 5), 0.25)),
            "u10": (("time", "y", "x"), np.full((5, 5, 5), 5.0)),
            "v10": (("time", "y", "x"), np.full((5, 5, 5), 2.0)),
            "t2m": (("time", "y", "x"), np.full((5, 5, 5), 270.0)),
            "mslp": (("time", "y", "x"), np.full((5, 5, 5), 101325.0)),
            "swh": (("time", "y", "x"), np.full((5, 5, 5), 1.5)),
            "uo": (("time", "y", "x"), np.full((5, 5, 5), 0.2)),
            "vo": (("time", "y", "x"), np.full((5, 5, 5), 0.1)),
            "lons": (("y", "x"), mg_lon),
            "lats": (("y", "x"), mg_lat),
        },
        coords={"time": times, "y": np.arange(5), "x": np.arange(5)},
    )

    store = EnvironmentStore(ds)
    state = store.get_state(15.0, -67.5, "2019-12-02")

    assert isinstance(state, EnvironmentState)
    assert state.sic == pytest.approx(0.25)
    assert state.u10_m_s == pytest.approx(5.0)
    assert state.v10_m_s == pytest.approx(2.0)
    assert state.wind_speed_knots > 0.0
    assert state.ocean_source == "glorys12"
    assert 0.0 <= state.overall_environment_risk <= 1.0
