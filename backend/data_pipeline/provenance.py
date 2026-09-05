"""Provenance manifests (brief §23): dataset -> preprocessing -> output traceability.

Each manifest is a JSON file under data/manifests/ that records source,
version, license, resolution, CRS, units, coverage, missing-data rate,
QC flags, and the exact preprocessing steps applied.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .qc import QCReport


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def new_manifest(product: str, source_cfg: dict, files: list[Path],
                 qc: QCReport, coverage: dict, preprocessing: list[str],
                 **extra) -> dict:
    """Assemble a manifest dict from product config, QC, and processing steps."""
    return {
        "product": product,
        "provider": source_cfg.get("provider"),
        "license": source_cfg.get("license"),
        "spatial_res": source_cfg.get("spatial_res_km") or source_cfg.get("spatial_res_deg"),
        "temporal_res": source_cfg.get("temporal_res"),
        "crs": source_cfg.get("crs"),
        "units": source_cfg.get("units"),
        "coverage_start": coverage.get("start"),
        "coverage_end": coverage.get("end"),
        "missing_rate": qc.missing_rate,
        "out_of_range_rate": qc.out_of_range_rate,
        "qc_flags": qc.flags,
        "preprocessing": preprocessing,
        "files": [{"path": str(p.relative_to(p.anchor) if False else p),
                   "sha256": sha256_file(p)} for p in files],
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **extra,
    }


def write_manifest(manifest: dict, manifests_dir: Path) -> Path:
    manifests_dir.mkdir(parents=True, exist_ok=True)
    out = manifests_dir / f"{manifest['product']}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return out


def read_manifest(product: str, manifests_dir: Path) -> dict:
    with open(manifests_dir / f"{product}.json", "r", encoding="utf-8") as f:
        return json.load(f)