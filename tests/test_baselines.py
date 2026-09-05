"""Phase 5 baseline tests: persistence SIC (FR-6), constant-velocity iceberg
(FR-9), shortest-path routing (FR-21), plus an end-to-end run over the real
feature store if present (skipped otherwise)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.baselines import iceberg, routing, sea_ice
from backend.baselines.metrics import haversine_km, mae, position_error_km, rmse


# ---------------------------------------------------------------- metrics ------
def test_mae_rmse_ignore_nan():
    t = np.array([1.0, 2.0, np.nan, 5.0])
    f = np.array([1.5, 2.5, 99.0, np.nan])  # NaN cells must not count
    # only 2 valid pairs: (1.0,1.5) and (2.0,2.5)
    assert mae(t, f) == pytest.approx(0.5)
    assert rmse(t, f) == pytest.approx(np.sqrt(0.25))


def test_haversine_symmetric_and_sane():
    d = haversine_km(76.19, -69.41, 11.73, -70.77)
    assert 2000.0 < d < 2600.0  # ~2330 km Bharati->Maitri
    assert d == pytest.approx(haversine_km(11.73, -70.77, 76.19, -69.41), abs=1e-9)


# ----------------------------------------------------------- sea-ice (FR-6) ---
def test_persistence_forecast_shift():
    sic = np.array([[[1.0], [2.0]], [[3.0], [4.0]], [[5.0], [6.0]], [[7.0], [8.0]]])
    truth, forecast = sea_ice.persistence_forecast(sic, 2)
    assert truth.shape == (2, 2, 1) and forecast.shape == (2, 2, 1)
    assert np.array_equal(forecast[0], sic[0])  # forecast[t] = sic[t-h]
    assert np.array_equal(truth[0], sic[2])


def test_persistence_perfect_when_constant():
    sic = np.tile(np.arange(6.0).reshape(1, 2, 3), (10, 1, 1))  # constant in time
    res = sea_ice.evaluate_persistence(sic, horizons=(1, 3))
    assert res[1]["mae"] == pytest.approx(0.0)
    assert res[3]["rmse"] == pytest.approx(0.0)


def test_persistence_error_grows_with_horizon_on_drift():
    rng = np.random.default_rng(0)
    sic = np.cumsum(rng.normal(0, 1.0, (30, 5, 5)), axis=0)  # random walk in time
    res = sea_ice.evaluate_persistence(sic, horizons=(1, 5))
    assert res[5]["rmse"] > res[1]["rmse"]


# ---------------------------------------------------------- iceberg (FR-9) -----
def _straight_track(lon0, lat0, dlon, dlat, hours, step_h=24):
    rows = []
    for i in range(int(hours / step_h) + 1):
        rows.append({"berg_id": "B1", "time": pd.Timestamp("2019-12-01") + pd.Timedelta(hours=i * step_h),
                     "lon": lon0 + dlon * i, "lat": lat0 + dlat * i})
    return pd.DataFrame(rows)


def test_constant_velocity_perfect_on_straight_track():
    # constant 0.5 deg/day east, 0.1 deg/day north -> baseline is exact
    tr = _straight_track(60.0, -68.0, 0.5, 0.1, hours=24 * 10)
    res = iceberg.evaluate_constant_velocity(tr, horizons_h=(24.0, 48.0, 72.0))
    for h in (24, 48, 72):
        assert res[h]["mean_km"] < 1.0


def test_constant_velocity_error_grows_with_horizon_on_curving_track():
    rows = []
    for i in range(11):
        rows.append({"berg_id": "B1", "time": pd.Timestamp("2019-12-01") + pd.Timedelta(hours=i * 24),
                     "lon": 60.0 + 0.5 * i + 0.02 * i * i,  # accelerating eastward
                     "lat": -68.0 + 0.1 * i})
    tr = pd.DataFrame(rows)
    res = iceberg.evaluate_constant_velocity(tr, horizons_h=(24.0, 72.0))
    assert res[72]["mean_km"] > res[24]["mean_km"]


# ---------------------------------------------------------- routing (FR-21) ---
def _walled_store():
    """Grid split N-S by a FULL-HEIGHT wall (cols 20-21) with one gap row at 15.
    The wall touches both grid edges so the gap is the only passage."""
    ny, nx = 30, 40
    lat = np.linspace(-75.0, -60.0, ny)
    lon = np.linspace(0.0, 95.0, nx)
    lon2d, lat2d = np.meshgrid(lon, lat)
    sic = np.zeros((1, ny, nx))  # open water everywhere (SIC 0)
    land = np.zeros((ny, nx), dtype=bool)
    land[:, 20] = True
    land[:, 21] = True
    land[15, 20:22] = False  # the only passage
    mask = routing.navigable_mask(sic[0], land)
    return lat2d, lon2d, mask


def test_shortest_path_through_gap():
    lat2d, lon2d, mask = _walled_store()
    y0, x0 = 28, 2   # bottom-left
    y1, x1 = 2, 37   # top-right
    r = routing.shortest_path(lat2d, lon2d, mask, (y0, x0), (y1, x1))
    assert r["found"]
    gap_used = any(y == 15 and 20 <= x <= 22 for y, x in r["path_xy"])
    assert gap_used  # only way across the wall
    for y, x in r["path_xy"]:
        assert mask[y, x]


def test_no_route_when_blocked():
    lat2d, lon2d, mask = _walled_store()
    m2 = mask.copy()
    m2[15, 20] = False  # close the gap: wall is now continuous top to bottom
    m2[15, 21] = False
    r = routing.shortest_path(lat2d, lon2d, m2, (28, 2), (2, 37))
    assert not r["found"]
    assert "no navigable path" in r["reason"]


def test_nearest_valid_cell_snaps_offshore():
    lat2d, lon2d, mask = _walled_store()
    # a target on land must snap to a navigable neighbour
    y, x = routing.nearest_valid_cell(lat2d, lon2d, mask, -70.0, 61.5)
    assert mask[y, x]


def test_position_error_metric():
    assert position_error_km(0.0, 0.0, 0.0, 1.0) == pytest.approx(111.19, rel=1e-3)


# --------------------------------------------------- end-to-end (real store) ---
def _real_store():
    p = ("data/processed/bharati_maitri_2019_20/features.nc")
    from pathlib import Path
    return Path(p)


def test_end_to_end_on_real_feature_store():
    import xarray as xr
    from backend.baselines.evaluate import run_baselines
    p = _real_store()
    if not p.exists():
        pytest.skip("real feature store not present (run the data pipeline first)")
    report = run_baselines(store_path=p)
    # persistence horizons populated
    h1 = report["sea_ice"]["horizons"][1]
    assert "mae" in h1 and "rmse" in h1 and h1["n_pairs"] > 90
    # routing finds Bharati -> Maitri on the real day-0 mask
    assert report["routing"]["result"]["found"]
    # iceberg evaluated (synthetic tracks labeled)
    assert report["iceberg"]["tracks_source"] == ["synthetic"]
