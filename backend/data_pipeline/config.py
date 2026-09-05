"""Config loading (configs/data_sources.yaml) and credential resolution.

Credentials are free-account credentials (CDS, CMEMS, Earthdata) read from
environment variables only — never committed (public repo hygiene).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs" / "data_sources.yaml"


@dataclass
class Credentials:
    cds_url: str | None = None
    cds_key: str | None = None
    cmems_username: str | None = None
    cmems_password: str | None = None
    earthdata_username: str | None = None
    earthdata_password: str | None = None

    @classmethod
    def from_env(cls) -> "Credentials":
        return cls(
            cds_url=os.environ.get("CDSAPI_URL"),
            cds_key=os.environ.get("CDSAPI_KEY"),
            cmems_username=os.environ.get("CMEMS_USERNAME"),
            cmems_password=os.environ.get("CMEMS_PASSWORD"),
            earthdata_username=os.environ.get("EARTHDATA_USERNAME"),
            earthdata_password=os.environ.get("EARTHDATA_PASSWORD"),
        )

    def for_access(self, access: str) -> bool:
        if access == "cds":
            return bool(self.cds_url and self.cds_key)
        if access == "cmems":
            return bool(self.cmems_username and self.cmems_password)
        if access == "http":
            return True
        return False  # manual / derived never need credentials


def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_scenario(cfg: dict, name: str) -> dict:
    try:
        return cfg["scenarios"][name]
    except KeyError:
        raise KeyError(f"unknown scenario {name!r}; available: {sorted(cfg['scenarios'])}")


def get_product(cfg: dict, product_id: str) -> dict:
    try:
        return cfg["products"][product_id]
    except KeyError:
        raise KeyError(f"unknown product {product_id!r}; available: {sorted(cfg['products'])}")


def scenario_products() -> list[str]:
    """Products used by the feature store (excluding manual/derived extras)."""
    return ["sic", "drift", "era5", "glorys12"]