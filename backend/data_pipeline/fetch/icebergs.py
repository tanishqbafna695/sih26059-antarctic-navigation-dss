"""Iceberg catalog fetches: BYU/NIC consolidated database and US NIC products.

Both are free. The BYU database URL is not script-stable; when a URL is not
configured, a ManualDownloadRequired error tells the team exactly what to do.
"""
from __future__ import annotations

from pathlib import Path

import requests

from . import FetchError, ManualDownloadRequired


def _download(url: str, out_path: Path, dry_run: bool = False) -> Path:
    if dry_run:
        print(f"[dry-run] http: would download {url} -> {out_path}")
        return out_path
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
    except requests.RequestException as e:
        raise FetchError(f"download failed for {url}: {e}") from e
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(r.content)
    return out_path


def fetch_byu_nic(product_cfg: dict, raw_dir: Path, dry_run: bool = False) -> Path:
    url = product_cfg.get("url")
    if not url:
        raise ManualDownloadRequired(
            "BYU/NIC iceberg database has no configured URL. Download the consolidated "
            "database (Budge & Long 2018) from www.scp.byu.edu/iceberg and place it at "
            "data/raw/icebergs/byu_nic.csv")
    return _download(url, raw_dir / "icebergs" / "byu_nic.csv", dry_run=dry_run)


def fetch_nic_recent(product_cfg: dict, raw_dir: Path, dry_run: bool = False) -> Path:
    url = product_cfg.get("url")
    if not url:
        raise ManualDownloadRequired(
            "US NIC Antarctic iceberg product URL not configured; see "
            "https://usicecenter.gov/Products/AntarcIcebergs")
    return _download(url, raw_dir / "icebergs" / "nic_recent.csv", dry_run=dry_run)