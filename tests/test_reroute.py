"""Phase 15 tests: dynamic re-routing (FR-30, FR-31, FR-32)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from backend.rerouting import RerouteThresholds, detect_changes, reroute
from backend.routing.costs import DayFieldsCache
from backend.routing.optimizer import arrival_times
from backend.vessel import PRESET_PROFILES


def _store(n_days=2):
    ny, nx = 12, 12
    lats = np.linspace(-70.0, -65.0, ny)
    lons = np.linspace(10.0, 40.0, nx)
    mg_lon, mg_lat = np.meshgrid(lons, lats)
    times = pd.date_range("2019-12-01", periods=n_days, freq="D")
    ds = xr.Dataset(
        {k: (("time", "y", "x"), np.full((n_days, ny, nx), v))
         for k, v in {"sic": 0.0, "u10": 0.0, "v10": 0.0, "t2m": 273.15,
                      "mslp": 101325.0, "swh": 0.0}.items()},
        coords={"time": times, "y": np.arange(ny), "x": np.arange(nx),
                "lon": (("y", "x"), mg_lon), "lat": (("y", "x"), mg_lat)},
    )
    ds.attrs["spacing_km"] = 25.0
    return ds


STRAIGHT = [(6, c) for c in range(1, 11)]
PROF = PRESET_PROFILES["polar_class_pc7"]


def _berg_at(ds, y, x, unc=8.0):
    return {"lon": float(ds["lon"].values[y, x]),
            "lat": float(ds["lat"].values[y, x]),
            "uncertainty_km": unc, "v_east_kmh": 0.0, "v_north_kmh": 0.0}


def test_arrival_times_monotonic_from_zero():
    ds = _store()
    cache = DayFieldsCache(ds, PROF, None, [], 0)
    t = arrival_times(cache, STRAIGHT)
    assert t[0] == 0.0 and t[-1] > 0.0
    assert all(b > a for a, b in zip(t[:-1], t[1:]))


def test_null_update_holds_with_no_trigger():
    ds = _store()
    # identical paths tie-break to "balanced": declare it the old winner so
    # the null update is genuinely a hold (engine recommends the same).
    n = reroute(ds, PROF, STRAIGHT, "balanced", 0, [], 3.0, 0, [],
                RerouteThresholds(), priority="balanced")
    assert n["outcome"] == "HOLDS"
    assert not n["changes"]["triggered"]
    assert n["new_recommendation"]["recommended"] == "balanced"
    assert set(n["old_remaining_if_staying"]) >= {"travel_time_h", "fuel_liters",
                                                 "mean_hazard"}


def test_new_berg_wall_forces_reroute_or_adjust():
    ds = _store()
    wall = [_berg_at(ds, 6, c) for c in (4, 5, 6)]
    n = reroute(ds, PROF, STRAIGHT, "fastest", 0, [], 3.0, 0, wall,
                RerouteThresholds(), priority="balanced")
    assert n["outcome"] in ("RE-ROUTE", "ADJUSTED")
    assert n["changes"]["triggered"]
    assert "fix" in n["changes"]["trigger_text"]
    assert n["change_explanation"]["explained"]
    assert n["new_explanation"]["explained"]


def test_detect_thresholds_are_configurable():
    shape = (4, 4)
    old_f = {"sic": np.zeros(shape), "berg_hazard": np.zeros(shape)}
    new_f = {"sic": np.full(shape, 0.03), "berg_hazard": np.zeros(shape)}
    path = [(y, x) for y in range(4) for x in range(4)]
    strict = detect_changes(old_f, new_f, path, [], [], RerouteThresholds())
    assert not strict["triggered"]  # 0.03 < default 0.05
    lax = detect_changes(old_f, new_f, path, [], [],
                         RerouteThresholds(min_sic_delta=0.01))
    assert lax["triggered"] and "sea-ice" in lax["trigger_text"]
    # berg-move threshold likewise
    ob = [{"lon": 20.0, "lat": -67.0, "uncertainty_km": 1.0}]
    nb = [{"lon": 20.2, "lat": -67.0, "uncertainty_km": 1.0}]  # ~8 km move
    assert not detect_changes(old_f, old_f, path, ob, nb,
                              RerouteThresholds())["triggered"]
    assert detect_changes(old_f, old_f, path, ob, nb, RerouteThresholds(
        min_berg_move_km=1.0))["triggered"]


def test_completed_voyage_needs_no_reroute():
    ds = _store()
    cache = DayFieldsCache(ds, PROF, None, [], 0)
    total = arrival_times(cache, STRAIGHT)[-1]
    n = reroute(ds, PROF, STRAIGHT, "fastest", 0, [], total + 1.0, 0, [])
    assert n["outcome"] == "COMPLETE"
