"""ERA5 single-levels fetch via the Copernicus Climate Data Store API.

Free registration (climate.copernicus.eu); credentials: CDSAPI_URL, CDSAPI_KEY
environment variables. Variables and dataset id come from configs/data_sources.yaml.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import CredentialsMissing


def _time_steps(scenario: dict) -> dict:
    start = pd.Timestamp(scenario["start"])
    end = pd.Timestamp(scenario["end"])
    days = pd.date_range(start, end, freq="D")
    return {
        "year": sorted(set(days.year.astype(str))),
        "month": sorted(set(days.month.astype(str))),
        "day": sorted(set(days.day.astype(str))),
    }


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
    request = {
        "product_type": "reanalysis",
        "variable": [v["cds"] for v in product_cfg["variables"]],
        **_time_steps(scenario),
        "time": ["00:00", "06:00", "12:00", "18:00"],
        "area": [box["north"], box["west"], box["south"], box["east"]],
        "data_format": "netcdf",
        "download_format": "unarchived",
    }
    out_dir = raw_dir / "era5"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "era5.nc"
    if dry_run:
        print(f"[dry-run] ERA5: would request {len(request['variable'])} variables "
              f"over {scenario['start']}..{scenario['end']} -> {target}")
        return target

    client = cdsapi.Client(url=cds_url, key=cds_key)
    client.retrieve(product_cfg["cds_dataset"], request, str(target))
    return target