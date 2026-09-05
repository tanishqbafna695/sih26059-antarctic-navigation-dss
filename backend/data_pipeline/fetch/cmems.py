"""CMEMS fetches: GLORYS12 ocean reanalysis and OSI SAF sea-ice products.

Free registration (data.marine.copernicus.eu); credentials: CMEMS_USERNAME,
CMEMS_PASSWORD environment variables. Product ids come from configs/data_sources.yaml
and should be re-verified in the MyOcean viewer if a fetch fails.
"""
from __future__ import annotations

from pathlib import Path

from . import CredentialsMissing


def _subset_args(scenario: dict, product_cfg: dict, variables: list[str]) -> dict:
    box = scenario["box"]
    return {
        "dataset_id": product_cfg["cmems_dataset"],
        "variables": variables,
        "minimum_longitude": box["west"],
        "maximum_longitude": box["east"],
        "minimum_latitude": box["south"],
        "maximum_latitude": box["north"],
        "start_datetime": scenario["start"] + "T00:00:00",
        "end_datetime": scenario["end"] + "T23:59:59",
    }


def fetch_cmems(scenario: dict, product_cfg: dict, raw_dir: Path, out_name: str,
                username: str | None, password: str | None,
                variables: list[str] | None = None, dry_run: bool = False) -> Path:
    try:
        import copernicusmarine  # noqa: PLC0415  (optional dependency)
    except ImportError as e:
        raise CredentialsMissing(
            "copernicusmarine not installed; run: "
            ".venv/Scripts/pip install copernicusmarine") from e
    if not (username and password):
        raise CredentialsMissing(
            "CMEMS credentials missing; set CMEMS_USERNAME and CMEMS_PASSWORD env vars "
            "(free registration at data.marine.copernicus.eu)")

    vars_to_get = variables or product_cfg["variables"]
    out_dir = raw_dir / out_name.split("_")[0]
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{out_name}.nc"
    if dry_run:
        print(f"[dry-run] CMEMS: would subset {product_cfg['cmems_dataset']} "
              f"({vars_to_get}) -> {target}")
        return target

    args = _subset_args(scenario, product_cfg, vars_to_get)
    copernicusmarine.subset(
        **args,
        output_directory=str(out_dir),
        output_filename=target.name,
        username=username,
        password=password,
    )
    return target


def fetch_osisaf_sic(scenario, product_cfg, raw_dir, creds, dry_run=False) -> Path:
    return fetch_cmems(scenario, product_cfg, raw_dir, "sic",
                       creds.cmems_username, creds.cmems_password, dry_run=dry_run)


def fetch_osisaf_drift(scenario, product_cfg, raw_dir, creds, dry_run=False) -> Path:
    return fetch_cmems(scenario, product_cfg, raw_dir, "drift",
                       creds.cmems_username, creds.cmems_password, dry_run=dry_run)


def fetch_glorys12(scenario, product_cfg, raw_dir, creds, dry_run=False) -> Path:
    return fetch_cmems(scenario, product_cfg, raw_dir, "glorys12",
                       creds.cmems_username, creds.cmems_password, dry_run=dry_run)