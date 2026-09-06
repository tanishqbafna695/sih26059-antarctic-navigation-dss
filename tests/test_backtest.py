"""Phase 16 tests: departure matrix + summary + stale clamp (SC-1..SC-7)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import xarray as xr

from backend.backtest import run_departure_matrix, summarize_matrix
from backend.routing.costs import DayFieldsCache, build_day_fields
from backend.vessel import PRESET_PROFILES


def _store(ice_cols=(), ice_val=0.5, n_days=2):
    ny, nx = 10, 12
    lats = np.linspace(-70.0, -65.0, ny)
    lons = np.linspace(10.0, 40.0, nx)
    mg_lon, mg_lat = np.meshgrid(lons, lats)
    sic = np.zeros((n_days, ny, nx))
    for c in ice_cols:
        sic[:, :, c] = ice_val
    times = pd.date_range("2019-12-01", periods=n_days, freq="D")
    ds = xr.Dataset(
        {k: (("time", "y", "x"), np.full((n_days, ny, nx), v))
         for k, v in {"u10": 0.0, "v10": 0.0, "t2m": 273.15,
                      "mslp": 101325.0, "swh": 0.0}.items()} |
        {"sic": (("time", "y", "x"), sic)},
        coords={"time": times, "y": np.arange(ny), "x": np.arange(nx),
                "lon": (("y", "x"), mg_lon), "lat": (("y", "x"), mg_lat)},
    )
    ds.attrs["spacing_km"] = 25.0
    return ds


def test_matrix_open_water_all_routed():
    ds = _store()
    m = run_departure_matrix(ds, [("polar_class_pc7", 0), ("polar_class_pc1", 0)], [])
    s = summarize_matrix(m)
    assert s["success_rate"] == 1.0
    assert s["sc7_no_route_ledger"] == []
    assert m["entries"]["polar_class_pc7@0"]["winner"] in ("fastest", "safest", "balanced")


def test_sc6_difference_and_sc7_ledger_on_ice_wall():
    ds = _store(ice_cols=(4, 5, 6, 7))  # blocks OW (limit 0.15), not PC1
    m = run_departure_matrix(ds, [("open_water_rv", 0), ("polar_class_pc1", 0)], [])
    assert not m["entries"]["open_water_rv@0"]["found"]
    assert m["entries"]["polar_class_pc1@0"]["found"]
    s = summarize_matrix(m)
    assert s["success_rate"] == 0.5
    assert len(s["sc6_vessel_differences"]) == 1
    assert s["sc6_vessel_differences"][0]["depart_day"] == 0
    assert s["sc7_no_route_ledger"][0]["vessel_id"] == "open_water_rv"


def test_stale_cache_freezes_at_cap_day():
    ds = _store()
    prof = PRESET_PROFILES["polar_class_pc7"]
    cache = DayFieldsCache(ds, prof, None, [], 0, max_day_index=0)
    assert cache.day(1000.0)["day_index"] == 0
    ref = build_day_fields(ds, 0, prof)
    assert np.array_equal(cache.day(1000.0)["sic"], ref["sic"],
                          equal_nan=True)


def test_summarize_empty_matrix():
    s = summarize_matrix({"entries": {}})
    assert s == {"n_cases": 0, "n_success": 0, "success_rate": 0.0,
                 "sc6_vessel_differences": [], "sc7_no_route_ledger": []}
