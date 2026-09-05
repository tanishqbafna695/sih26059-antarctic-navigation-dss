"""Fetch a multi-season OSI SAF SIC record to train the Phase 6 sea-ice model.

The single 2019-20 demo window (106 days) cannot support learning seasonal
evolution, so the Phase 3 plan (OSI-450/AMSR CDR, 2002-2020 via CMEMS) is
used here: for each Dec-Mar season in a chosen range we subset the same
product/box, regrid onto the common 25 km grid, and concatenate into one
labeled dataset with season + day-in-season coordinates.

The demo window (2019-12-01..2020-03-15) is EXCLUDED from training: it is
the held-out evaluation season (the existing real feature store).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from .. import provenance
from ..config import ROOT, Credentials, get_product, load_config
from ..grid import common_grid_for_box, regrid_product
from ..qc import run_qc
from . import cmems

BOX = {"south": -75.0, "north": -55.0, "west": 0.0, "east": 95.0}
GRID_KW = {"epsg": 3412, "spacing_km": 25.0, "margin_km": 50.0}
SEASON_START_MONTH_DAY = (12, 1)
SEASON_END_MONTH_DAY = (3, 15)
RAW_DIR = ROOT / "data" / "raw" / "training_sic"
OUT_FILE = ROOT / "data" / "processed" / "training_sic_seasons.nc"


def season_windows(start_year: int, end_year: int, exclude: tuple[int, int] = (2019, 2020)) -> list[tuple]:
    """(start, end) ISO strings for each Dec(start)-Mar(start+1) season."""
    out = []
    for y in range(start_year, end_year + 1):
        start = pd.Timestamp(year=y, month=12, day=1)
        end = pd.Timestamp(year=y + 1, month=3, day=15)
        if start.year == exclude[0]:
            continue  # held-out demo season
        out.append((start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")))
    return out


def _season_scenario(start: str, end: str) -> dict:
    return {"name": f"training {start}..{end}", "start": start, "end": end,
            "box": BOX}


def build_training_dataset(seasons: list[tuple] | None = None,
                           years: tuple[int, int] = (2003, 2018)) -> Path:
    """Fetch SIC for each season, regrid, concatenate, save. Returns out path."""
    cfg = load_config()
    pcfg = get_product(cfg, "sic")
    grid = common_grid_for_box(BOX, **GRID_KW)
    creds = Credentials.from_env()
    if not (creds.cmems_username and creds.cmems_password):
        raise RuntimeError("CMEMS credentials missing (CMEMS_USERNAME/PASSWORD env vars)")
    seasons = seasons or season_windows(*years)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    frames: list[xr.Dataset] = []
    for start, end in seasons:
        scen = _season_scenario(start, end)
        # fetch into a season-specific file so we never overwrite the primary
        # 2019-20 raw SIC that the main feature-store pipeline depends on
        tag = f"{start}..{end}"
        raw = cmems.fetch_cmems(scen, pcfg, RAW_DIR.parent, f"sic_{tag}",
                                creds.cmems_username, creds.cmems_password)
        ds = xr.open_dataset(raw, engine="h5netcdf")
        if "valid_time" in ds.dims:
            ds = ds.rename({"valid_time": "time"})
        # regrid onto the common grid (mirrors process_product for sic)
        da = ds["ice_conc"] if "ice_conc" in ds else next(iter(ds.data_vars.values()))
        vals = regrid_product(da, grid, "rectilinear")
        vals = np.clip(vals / 100.0, 0.0, 1.0)  # % -> fraction
        n = len(ds.time)
        day_in_season = np.arange(n)
        fr = xr.Dataset(
            {"sic": (("time", "y", "x"), vals)},
            coords={"time": ds["time"].values, "y": grid.y, "x": grid.x},
        )
        fr = fr.assign_coords(day_in_season=("time", day_in_season))
        fr.attrs["season_start"] = start
        fr.attrs["season_end"] = end
        frames.append(fr)
        ds.close()
        print(f"  fetched+regridded {start}..{end}: {n} days")

    combined = xr.concat(frames, dim="time")
    combined = combined.assign_coords(season=(
        "time", [str(pd.Timestamp(t).year) for t in combined.time.values]))
    # a day counter resetting each season for phase-based features
    combined["season_id"] = (("time",),
                             np.asarray(pd.factorize(pd.Index([str(pd.Timestamp(t).year)
                                                               for t in combined.time.values]))[0]))
    combined.attrs["n_seasons"] = len(frames)
    combined.attrs["epsg"] = grid.epsg
    combined.attrs["spacing_km"] = grid.spacing_km
    combined.attrs["held_out_season"] = "2019-2020 (excluded by builder)"
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    combined.to_netcdf(OUT_FILE, engine="h5netcdf", invalid_netcdf=True)

    # provenance manifest (repo-relative paths)
    qc = run_qc("training_sic", combined["sic"].values, vmin=0.0, vmax=1.0)
    manifest = provenance.new_manifest(
        "training_sic", pcfg,
        [Path(x) for x in sorted(RAW_DIR.parent.glob("sic/sic_20*.nc"))][:3],
        qc, coverage={"start": seasons[0][0], "end": seasons[-1][1]},
        preprocessing=["subset per season", "regrid to EPSG:3412 25 km",
                       "concatenate seasons", "% -> fraction"],
        repo_root=ROOT,
    )
    provenance.write_manifest(manifest, ROOT / "data" / "manifests")
    print(f"training dataset: {OUT_FILE} ({combined.sizes})")
    return OUT_FILE


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Build multi-season SIC training dataset")
    ap.add_argument("--start-year", type=int, default=2003,
                    help="first season's Dec year")
    ap.add_argument("--end-year", type=int, default=2018,
                    help="last season's Dec year (2019-20 is held out)")
    args = ap.parse_args(argv)
    build_training_dataset(years=(args.start_year, args.end_year))


if __name__ == "__main__":
    main()
