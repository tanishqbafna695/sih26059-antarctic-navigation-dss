"""Phase 4 pipeline tests: CRS, temporal, grid, QC, features, provenance,
plus a credential-free end-to-end run over synthetic data."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import xarray as xr

from backend.data_pipeline import crs, features, provenance, temporal
from backend.data_pipeline.fetch.fetch_all import run_pipeline
from backend.data_pipeline.grid import common_grid_for_box, regrid_product
from backend.data_pipeline.qc import missing_rate, range_failure_rate, run_qc

BOX = {"south": -75.0, "north": -55.0, "west": 0.0, "east": 95.0}
GRID_KW = {"epsg": 3412, "spacing_km": 25.0, "margin_km": 50.0}


# ---------------------------------------------------------------- CRS ----------
def test_crs_roundtrip():
    lon, lat = 60.0, -68.0
    x, y = crs.lonlat_to_ps(lon, lat)
    lon2, lat2 = crs.ps_to_lonlat(x, y)
    assert abs(lon2 - lon) < 1e-6
    assert abs(lat2 - lat) < 1e-6


def test_box_to_ps_extent_covers_box():
    grid = common_grid_for_box(BOX, **GRID_KW)
    for lon, lat in [(5.0, -56.0), (90.0, -60.0), (40.0, -74.0)]:
        x, y = crs.lonlat_to_ps(lon, lat)
        assert grid.x[0] <= x <= grid.x[-1]
        assert grid.y[0] <= y <= grid.y[-1]


def test_common_grid_spacing():
    grid = common_grid_for_box(BOX, **GRID_KW)
    assert np.isclose(np.diff(grid.x)[0], 25000.0)
    assert grid.ny > 0 and grid.nx > 0
    assert grid.lons().shape == (grid.ny, grid.nx)


# ---------------------------------------------------------------- grid ---------
def test_regrid_rectilinear_constant_field():
    # Note: the PS bounding rectangle extends beyond the lon/lat box (curved
    # mapping), so cells outside the box are NaN by design and masked in routing.
    grid = common_grid_for_box(BOX, **GRID_KW)
    lat = np.linspace(-75.0, -55.0, 40)  # descending, like CDS/CMEMS files
    lon = np.linspace(0.0, 95.0, 60)
    da = xr.DataArray(np.full((40, 60), 7.0), dims=("latitude", "longitude"),
                      coords={"latitude": lat, "longitude": lon})
    out = regrid_product(da, grid, "rectilinear")
    assert out.shape == (grid.ny, grid.nx)
    assert np.allclose(out[~np.isnan(out)], 7.0, atol=1e-6)  # valid cells exact
    assert np.isnan(out).sum() > 0                           # outside-box cells NaN
    # a cell near the box center must be valid
    cy, cx = np.unravel_index(np.nanargmin(np.abs(grid.lats() + 65.0)
                                           + np.abs(grid.lons() - 47.5)), out.shape)
    assert not np.isnan(out[cy, cx])


def test_regrid_polar_scattered():
    grid = common_grid_for_box(BOX, **GRID_KW)
    x = np.linspace(grid.x[0], grid.x[-1], 30)
    y = np.linspace(grid.y[0], grid.y[-1], 25)
    xx, yy = np.meshgrid(x, y)
    lon, lat = crs.ps_to_lonlat(xx, yy)
    da = xr.DataArray(np.full((25, 30), 3.0), dims=("y", "x"),
                      coords={"y": y, "x": x})
    da.attrs["epsg"] = 3412
    out = regrid_product(da, grid, "polar", src_epsg=3412)
    assert out.shape == (grid.ny, grid.nx)
    assert np.nanmean(out) > 2.99


# ------------------------------------------------------------- temporal --------
def test_resample_daily_means():
    times = pd.date_range("2019-12-01", periods=8, freq="6h")
    ds = xr.Dataset({"v": ("time", [0.0, 2.0, 4.0, 6.0, 1.0, 3.0, 5.0, 7.0])},
                    coords={"time": times})
    daily = temporal.resample_daily(ds)
    assert len(daily.time) == 2
    assert daily["v"].values.tolist() == [3.0, 4.0]


def test_align_time_axis_fills_gaps():
    times = pd.date_range("2019-12-01", periods=2, freq="D")
    ds = xr.Dataset({"v": ("time", [1.0, 2.0])}, coords={"time": times})
    aligned = temporal.align_time_axis(ds, "2019-12-01", "2019-12-04")
    assert len(aligned.time) == 4
    assert np.isnan(aligned["v"].values[2])


# ---------------------------------------------------------------- qc ----------
def test_qc_range_and_missing():
    arr = np.array([0.0, 50.0, 150.0, np.nan])
    assert missing_rate(arr) == 0.25
    assert range_failure_rate(arr, 0.0, 100.0) == 1.0 / 3.0
    rep = run_qc("test", arr, vmin=0.0, vmax=100.0, flags=["x"])
    assert rep.product == "test" and rep.flags == ["x"]


# ------------------------------------------------------------- features --------
def test_ice_edge_distance():
    ice = np.zeros((11, 11), dtype=bool)  # odd size so the ice cell is centered
    ice[5, 5] = True
    d = features.ice_edge_distance(ice, spacing_km=25.0)
    assert d[5, 5] == 0.0
    assert d[0, 0] > d[4, 4] > 0.0
    assert d[0, 0] == d[10, 10]  # symmetric about the centered ice cell


def test_ice_mask_respects_land():
    sic = np.array([0.1, 0.9])
    land = np.array([False, True])
    m = features.ice_mask(sic, land)
    assert m.tolist() == [False, False]


# ------------------------------------------------------------ provenance -------
def test_manifest_roundtrip(tmp_path):
    f = tmp_path / "a.nc"
    f.write_bytes(b"0123456789abcdef")
    rep = run_qc("sic", np.array([1.0, np.nan]), vmin=0.0, vmax=1.0)
    m = provenance.new_manifest("sic", {"provider": "OSI SAF", "license": "CC-BY-4.0"},
                                [f], rep, coverage={"start": "2019-12-01", "end": "2020-03-15"},
                                preprocessing=["regrid"])
    out = provenance.write_manifest(m, tmp_path / "manifests")
    m2 = provenance.read_manifest("sic", tmp_path / "manifests")
    assert m2["provider"] == "OSI SAF"
    assert m2["missing_rate"] == 0.5
    assert m2["files"][0]["sha256"] == provenance.sha256_file(f)
    assert out.exists()


def test_manifest_paths_are_repo_relative(tmp_path):
    """Privacy: committed manifests must never embed absolute machine paths."""
    from pathlib import Path as P
    import backend.data_pipeline.provenance as prov
    from backend.data_pipeline import config as cfg_mod

    f = cfg_mod.ROOT / "data" / "manifests" / ".gitkeep"  # a real in-repo file
    rep = run_qc("x", np.array([1.0]), vmin=0.0, vmax=1.0)
    m = prov.new_manifest("x", {"provider": "p"}, [f], rep,
                          coverage={}, preprocessing=[], repo_root=cfg_mod.ROOT)
    stored = m["files"][0]["path"]
    assert not P(stored).is_absolute()          # relative, not C:\\Users\\...
    assert str(f).endswith(str(stored))          # still points at the right file
    assert (cfg_mod.ROOT / stored).resolve() == f.resolve()


# ------------------------------------------------------- end-to-end (synthetic) -
def test_synthetic_end_to_end(tmp_path):
    run_pipeline("bharati_maitri_2019_20", tmp_path, synthetic=True, synth_days=5)
    processed = tmp_path / "processed" / "bharati_maitri_2019_20"

    assert (processed / "features.nc").exists()
    store = xr.open_dataset(processed / "features.nc", engine="h5netcdf")
    expected = {"sic", "ice_mask", "edge_dist", "drift_u", "drift_v",
                "u10", "v10", "t2m", "mslp", "sst", "swh", "mwd", "mwp",
                "uo", "vo", "thetao", "zos", "landmask"}
    assert expected <= set(store.data_vars)
    assert store.sic.shape == (5, store.y.size, store.x.size)
    assert float(store.sic.min()) >= 0.0
    assert float(store.sic.max()) <= 1.0
    assert float(store.edge_dist.min()) == 0.0
    assert bool(store.landmask.dtype == bool)

    # provenance manifests written
    for pid in ("sic", "drift", "era5", "glorys12", "features"):
        assert (tmp_path / "manifests" / f"{pid}.json").exists()
    manifest = json.loads((tmp_path / "manifests" / "sic.json").read_text())
    assert manifest["synthetic"] is True

    # synthetic iceberg tracks labeled
    bergs = pd.read_csv(tmp_path / "synthetic" / "raw" / "icebergs_synthetic.csv")
    assert set(bergs["source"]) == {"synthetic"}
    assert len(bergs) == 3 * 5