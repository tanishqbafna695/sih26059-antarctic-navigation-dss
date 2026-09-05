"""GEBCO bathymetry fetch (optional, CC-BY-4.0).

The GEBCO download app does not expose a stable anonymous API, so the default
path is manual placement of the global or subset netCDF into data/raw/gebco/.
A configured URL is used when available.
"""
from __future__ import annotations

from pathlib import Path

import requests

from . import FetchError, ManualDownloadRequired


def fetch_gebco(product_cfg: dict, raw_dir: Path, dry_run: bool = False) -> Path:
    url = product_cfg.get("url")
    out_path = raw_dir / "gebco" / "gebco_2023.nc"
    if not url:
        raise ManualDownloadRequired(
            "GEBCO has no scriptable URL configured. Download the GEBCO 2023 grid "
            "(or a subset) from download.gebco.net and place it at "
            "data/raw/gebco/gebco_2023.nc (CC-BY-4.0)")
    if dry_run:
        print(f"[dry-run] GEBCO: would download {url} -> {out_path}")
        return out_path
    try:
        r = requests.get(url, timeout=600)
        r.raise_for_status()
    except requests.RequestException as e:
        raise FetchError(f"GEBCO download failed: {e}") from e
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(r.content)
    return out_path