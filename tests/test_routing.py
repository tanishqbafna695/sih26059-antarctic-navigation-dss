"""Phase 12 tests: multi-objective time-aware routing (FR-22, FR-23, FR-24)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from backend.environment.ocean import ocean_severity_index
from backend.environment.weather import beaufort_scale, weather_severity_index
from backend.hazard import compute_iceberg_hazard, compute_sea_ice_hazard
from backend.routing import NoRouteFound, WEIGHT_PRESETS, plan_routes
from backend.routing.costs import (
    DayFieldsCache,
    beaufort_grid,
    build_day_fields,
    ocean_severity_grid,
    weather_severity_grid,
)
from backend.routing.optimizer import fuel_rate_for
from backend.vessel import PRESET_PROFILES, calculate_effective_speed, calculate_fuel_rate


def _mini_store(ny=20, nx=25, n_days=3, sic_fn=None, u10_val=5.0,
                v10_val=2.0, swh_val=1.0) -> xr.Dataset:
    """Tiny synthetic feature store on a lat/lon grid for routing tests."""
    lats = np.linspace(-70.0, -65.0, ny)
    lons = np.linspace(10.0, 40.0, nx)
    mg_lon, mg_lat = np.meshgrid(lons, lats)
    times = pd.date_range("2019-12-01", periods=n_days, freq="D")
    sic = np.zeros((n_days, ny, nx))
    for d in range(n_days):
        sic[d] = sic_fn(d, mg_lon, mg_lat) if sic_fn else 0.0
    ds = xr.Dataset(
        {
            "sic": (("time", "y", "x"), sic),
            "u10": (("time", "y", "x"), np.full((n_days, ny, nx), u10_val)),
            "v10": (("time", "y", "x"), np.full((n_days, ny, nx), v10_val)),
            "t2m": (("time", "y", "x"), np.full((n_days, ny, nx), 270.0)),
            "mslp": (("time", "y", "x"), np.full((n_days, ny, nx), 101325.0)),
            "swh": (("time", "y", "x"), np.full((n_days, ny, nx), swh_val)),
        },
        coords={"time": times, "y": np.arange(ny), "x": np.arange(nx),
                "lon": (("y", "x"), mg_lon), "lat": (("y", "x"), mg_lat)},
    )
    ds.attrs["spacing_km"] = 25.0
    return ds


# -------------------------------- vector-vs-scalar consistency ----------
def test_beaufort_grid_matches_scalar():
    ws = np.array([0.5, 5.0, 15.0, 30.0, 65.0])
    assert beaufort_grid(ws).tolist() == [beaufort_scale(float(v)) for v in ws]


def test_weather_severity_grid_matches_scalar():
    u = np.array([2.0, 20.0])
    v = np.array([2.0, 15.0])
    sev, _, _ = weather_severity_grid(u, v, np.array([275.0, 255.0]), np.array([0.5, 5.0]))
    assert sev[0] == pytest.approx(weather_severity_index(2.0, 2.0, 275.0, 0.5))
    assert sev[1] == pytest.approx(weather_severity_index(20.0, 15.0, 255.0, 5.0))


def test_ocean_severity_grid_matches_scalar():
    cs = np.array([0.1, 0.5, 1.2])
    assert np.allclose(ocean_severity_grid(cs),
                       [ocean_severity_index(float(v)) for v in cs])


def test_ice_hazard_in_day_fields_matches_scalar():
    ds = _mini_store()
    ds["sic"].values[0, 3, 4] = 0.40
    prof = PRESET_PROFILES["polar_class_pc7"]
    f = build_day_fields(ds, 0, prof)
    h, blocked, _ = compute_sea_ice_hazard(0.40, max_sic_limit=0.60)
    assert f["ice_hazard"][3, 4] == pytest.approx(h)
    assert bool(f["blocked"][3, 4]) == blocked


def test_fuel_rate_matches_vessel_module():
    prof = PRESET_PROFILES["polar_class_pc1"]
    assert fuel_rate_for(prof, 10.0, 0.5, 4) == pytest.approx(
        calculate_fuel_rate(prof, 10.0, 0.5, 4))
    assert fuel_rate_for(prof, 15.0, 0.0, 0) == pytest.approx(
        calculate_fuel_rate(prof, 15.0, 0.0, 0))


def test_base_speed_matches_vessel_module_zero_current():
    ds = _mini_store()
    prof = PRESET_PROFILES["polar_class_pc7"]
    ds["sic"].values[0, 2, 2] = 0.30
    f = build_day_fields(ds, 0, prof)
    v_scalar = calculate_effective_speed(prof, 0.30, wind_speed_kts=0.0,
                                         swh_m=0.0, current_along_track_kts=0.0)
    # base_speed excludes current; recompute scalar with the cell's own weather
    ws = float(f["wind_kts"][2, 2])
    v2 = calculate_effective_speed(prof, 0.30, wind_speed_kts=ws,
                                   swh_m=1.0, current_along_track_kts=0.0)
    assert float(f["base_speed_kts"][2, 2]) == pytest.approx(v2)
    assert v_scalar > 0.0  # sanity: cell is navigable for PC7


def test_iceberg_hazard_single_point_matches_scalar():
    bergs = [{"lon": 20.0, "lat": -67.5, "uncertainty_km": 1.0}]
    assert compute_iceberg_hazard(20.0, -67.5, bergs) == pytest.approx(1.0)


# -------------------------------- time-awareness (FR-23) -----------------
def test_day_cache_maps_elapsed_hours_to_days():
    ds = _mini_store(n_days=3)
    prof = PRESET_PROFILES["polar_class_pc7"]
    cache = DayFieldsCache(ds, prof, depart_day_index=0)
    assert cache.day(0.0)["day_index"] == 0
    assert cache.day(30.0)["day_index"] == 1
    assert cache.day(10_000.0)["day_index"] == 2  # clamped to store end


def test_day_fields_change_across_days():
    def sic_fn(d, lon, lat):
        base = np.zeros_like(lon)
        if d >= 1:
            base[:, 10:15] = 0.9  # ice wall appears on day 1
        return base
    ds = _mini_store(n_days=2, sic_fn=sic_fn)
    prof = PRESET_PROFILES["polar_class_pc7"]
    f0 = build_day_fields(ds, 0, prof)
    f1 = build_day_fields(ds, 1, prof)
    assert not bool(f0["blocked"][10, 12])
    assert bool(f1["blocked"][10, 12])


# -------------------------------- multi-objective (FR-22) ----------------
def _gradient_store():
    """Single-day static store (all arrivals clamp to day 0, so each weight
    set's optimum is exact), dead-calm weather (zero background risk so the
    trade-off is clean), with a perpendicular iceberg-danger wall across most
    of the domain: the direct crossing is short but risky, the eastern gap
    detour is safe but long. Start is south of the wall, goal north."""
    return _mini_store(ny=20, nx=25, n_days=1, u10_val=0.0, v10_val=0.0,
                       swh_val=0.0)


_BERG_ON_PATH = [
    {"lon": lon, "lat": -67.5, "uncertainty_km": 8.0,
     "v_east_kmh": 0.0, "v_north_kmh": 0.0}
    for lon in (13.0, 16.5, 20.0, 23.5, 27.0, 30.5)
]


def _risk_sum(r):
    return r["mean_hazard"] * r["n_cells"]


def test_pure_objectives_are_optimal():
    """On static fields Dijkstra is exact: the risk-only optimum has the
    minimum risk-sum and the time-only optimum the minimum time (FR-22)."""
    ds = _gradient_store()
    prof = PRESET_PROFILES["polar_class_pc7"]
    plan = plan_routes(
        ds, (-69.5, 11.0), (-65.5, 39.0), prof, depart_day_index=0,
        weight_sets={"risk_only": {"alpha": 1.0, "beta": 0.0, "gamma": 0.0},
                     "time_only": {"alpha": 0.0, "beta": 1.0, "gamma": 0.0}},
        icebergs=_BERG_ON_PATH)
    rk, tm = plan["routes"]["risk_only"], plan["routes"]["time_only"]
    assert _risk_sum(rk) <= _risk_sum(tm)
    assert tm["travel_time_h"] <= rk["travel_time_h"]


def test_fastest_vs_safest_differ_with_tradeoff():
    ds = _gradient_store()
    prof = PRESET_PROFILES["polar_class_pc7"]
    plan = plan_routes(ds, (-69.5, 11.0), (-65.5, 39.0), prof,
                       depart_day_index=0, icebergs=_BERG_ON_PATH)
    assert set(plan["routes"]) == {"fastest", "safest", "balanced"}
    fast, safe = plan["routes"]["fastest"], plan["routes"]["safest"]
    assert fast["path_xy"] != safe["path_xy"]  # weights change the answer
    assert safe["mean_hazard"] < fast["mean_hazard"]
    assert fast["travel_time_h"] <= safe["travel_time_h"]
    for r in plan["routes"].values():
        assert 0.0 <= r["mean_hazard"] <= 1.0
        assert r["travel_time_h"] > 0 and r["fuel_liters"] > 0
    assert "overall_confidence" in plan["confidence"]


def test_weight_presets_are_configurable():
    ds = _gradient_store()
    prof = PRESET_PROFILES["polar_class_pc7"]
    custom = {"risk_only": {"alpha": 1.0, "beta": 0.0, "gamma": 0.0}}
    plan = plan_routes(ds, (-69.5, 11.0), (-65.5, 39.0), prof,
                       depart_day_index=0, weight_sets=custom,
                       icebergs=_BERG_ON_PATH)
    assert set(plan["routes"]) == {"risk_only"}


# -------------------------------- no-route (FR-24) -----------------------
def test_no_route_raises_with_out8_details():
    ds = _mini_store()
    ds["sic"].values[:] = 0.9  # solid pack: PC7 (limit 0.60) cannot move
    prof = PRESET_PROFILES["polar_class_pc7"]
    with pytest.raises(NoRouteFound) as ei:
        plan_routes(ds, (-69.5, 11.0), (-65.5, 39.0), prof)
    assert "no acceptable route" in str(ei.value).lower()
    assert ei.value.details["blocked_fraction"] > 0.9


def test_blocked_cells_never_in_path():
    def sic_fn(d, lon, lat):
        base = np.zeros_like(lon)
        base[8:12, :] = 0.9  # full-width wall, no gap
        return base
    ds = _mini_store(n_days=2, sic_fn=sic_fn)
    prof = PRESET_PROFILES["polar_class_pc7"]
    # start below wall, goal above wall -> wall is impassable
    with pytest.raises(NoRouteFound):
        plan_routes(ds, (-69.5, 25.0), (-65.5, 25.0), prof)


# -------------------------------- end-to-end (real store) ----------------
def test_end_to_end_on_real_feature_store():
    p = Path("data/processed/bharati_maitri_2019_20/features.nc")
    if not p.exists():
        pytest.skip("real feature store not present (run the data pipeline first)")
    import xarray as xr
    ds = xr.open_dataset(p, engine="h5netcdf")
    prof = PRESET_PROFILES["polar_class_pc7"]
    # depart day 45 (2020-01-15, mid-season open corridor; day 0 is ice-locked
    # for PC7 -- recorded in the Phase 12 gate log)
    plan = plan_routes(ds, (-69.41, 76.19), (-70.77, 11.73), prof,
                       depart_day_index=45, icebergs=[])
    ds.close()
    assert set(plan["routes"]) == set(WEIGHT_PRESETS)
    for r in plan["routes"].values():
        assert r["travel_time_h"] > 0 and r["fuel_liters"] > 0
        assert 0.0 <= r["mean_hazard"] <= 1.0
        assert r["n_cells"] > 10
    assert plan["confidence"]["overall_confidence"] > 0.0
