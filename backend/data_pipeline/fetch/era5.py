"""ERA5 single-levels fetch via the Copernicus Climate Data Store API.

Free registration (climate.copernicus.eu); credentials: CDSAPI_URL, CDSAPI_KEY
environment variables. Variables and dataset id come from configs/data_sources.yaml.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import CredentialsMissing


def _time_steps(scenario: dict) -> list[dict]:
    """Split a scenario window into CDS requests, one per (year, month).

    The CDS API cross-products the year/month/day lists it receives, so passing
    Dec 2019..Mar 2020 as year=[2019, 2020] x month=[12, 1, 2, 3] would also
    fetch Jan-Mar 2019 and Dec 2020. Splitting by month keeps the request
    bounded to the actual window (and each request gets that month's days).
    """
    start = pd.Timestamp(scenario["start"])
    end = pd.Timestamp(scenario["end"])
    requests: list[dict] = []
    cursor = start
    while cursor <= end:
        last_day = (cursor + pd.offsets.MonthEnd(0)).day
        month_end = min(cursor.replace(day=last_day), end)
        days = pd.date_range(cursor, month_end, freq="D")
        requests.append({
            "year": str(cursor.year),
            "month": str(cursor.month),
            "day": sorted(set(days.day.astype(str))),
        })
        cursor = month_end + pd.Timedelta(days=1)
    return requests


def fetch_era5(scenario: dict, product_cfg: dict, raw_dir: Path,
               cds_url: str | None, cds_key: str | None, dry_run: bool = False) -> Path:
    try:
        import cdsapi  # noqa: PLC0415  (optional dependency)
    except ImportError as e:
        raise CredentialsMissing(
            "cdsapi not installed; run: .venv/Scripts/pip install cdsapi") from e
    if not (cds_url and cds_key):
        raise CredentialsMissing(
            "CDS credentials missing; set CDSAPI_URL and CDSAPI_KEY env vars "
            "(free registration at climate.copernicus.eu)")

    box = scenario["box"]
    monthly = _time_steps(scenario)
    out_dir = raw_dir / "era5"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "era5.nc"
    if dry_run:
        print(f"[dry-run] ERA5: would request {len(product_cfg['variables'])} variables "
              f"over {scenario['start']}..{scenario['end']} "
              f"({len(monthly)} monthly requests) -> {target}")
        return target

    client = cdsapi.Client(url=cds_url, key=cds_key)
    parts: list[Path] = []
    for i, ts in enumerate(monthly):
        request = {
            "product_type": "reanalysis",
            "variable": [v["cds"] for v in product_cfg["variables"]],
            **ts,
            "time": ["00:00", "06:00", "12:00", "18:00"],
            "area": [box["north"], box["west"], box["south"], box["east"]],
            "data_format": "netcdf",
            "download_format": "unarchived",
        }
        part = out_dir / f"era5_{ts['year']}_{ts['month']}.zip"
        print(f"[era5] month {ts['year']}-{ts['month']:>2}: {len(ts['day'])} days...")
        client.retrieve(product_cfg["cds_dataset"], request, str(part))
        parts.append(part)

    # Each monthly archive contains several stream NetCDFs (e.g. oper 0.25 deg +
    # wave 0.5 deg) that share timestamps but carry different variables/grids.
    # Per month: interpolate every stream onto the finest grid, then MERGE
    # (variables side by side, timestamps shared). Across months: concat.
    import zipfile  # noqa: PLC0415
    import xarray as xr  # noqa: PLC0415
    merged_ds = None
    for part in parts:
        month_files: list[Path] = []
        if zipfile.is_zipfile(part):
            with zipfile.ZipFile(part, "r") as zf:
                nc_names = [n for n in zf.namelist() if n.endswith(".nc")]
                zf.extractall(out_dir)
            part.unlink()
            month_files = [out_dir / n for n in nc_names]
        else:
            month_files = [part]
        stream_ds = [xr.open_dataset(p) for p in month_files]
        # Finest grid = most latitude points within this month's set.
        finest = max(stream_ds, key=lambda d: d.sizes.get("latitude", 0))
        target_grid = {"latitude": finest["latitude"].values,
                       "longitude": finest["longitude"].values}
        aligned = [d if d is finest else d.interp(latitude=target_grid["latitude"],
                                                  longitude=target_grid["longitude"])
                   for d in stream_ds]
        month_ds = xr.merge(aligned, join="inner", compat="override")
        for d in stream_ds:
            d.close()
        merged_ds = month_ds if merged_ds is None else xr.concat([merged_ds, month_ds], dim="valid_time")
        month_ds.close()
    if merged_ds is None:
        raise RuntimeError("ERA5 download produced no data")
    merged_ds.to_netcdf(target)
    merged_ds.close()
    return target

    # CDS may return a ZIP archive; extract if so
    import zipfile  # noqa: PLC0415
    if zipfile.is_zipfile(target):
        import xarray as xr  # noqa: PLC0415
        with zipfile.ZipFile(target, "r") as zf:
            nc_names = [n for n in zf.namelist() if n.endswith(".nc")]
            zf.extractall(out_dir)
        target.unlink()  # remove the zip
        # Merge all extracted NetCDF files on the time axis (same timestamps,
        # different variables). Different native grids are fine: the pipeline
        # regrids each variable individually onto the common grid.
        datasets = [xr.open_dataset(out_dir / n) for n in nc_names]
        if len(datasets) > 1:
            merged = xr.merge(datasets, join="inner", compat="override")
        else:
            merged = datasets[0]
        for ds in datasets:
            ds.close()
        merged.to_netcdf(target)
        merged.close()
    return target