"""Phase 5 evaluation harness: run all baselines on a feature store.

Produces a JSON report under data/baselines/ containing:

- sea_ice: persistence MAE/RMSE at 1..5 day horizons     (FR-6)
- iceberg: constant-velocity position error at 24/48/72h (FR-9)
- routing: shortest-path route Bharati->Maitri           (FR-21)

Everything is recorded with inputs/parameters so results are reproducible
(NFR-5) and every headline number is traceable to a run (claim discipline).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from ..data_pipeline.config import ROOT
from . import iceberg, routing, sea_ice

DEFAULT_STORE = ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"
DEFAULT_TRACKS = ROOT / "data" / "synthetic" / "raw" / "icebergs_synthetic.csv"
DEFAULT_OUT = ROOT / "data" / "baselines"
BHARATI = (-69.41, 76.19)
MAITRI = (-70.77, 11.73)


def _iceberg_report(tracks_csv: Path) -> dict:
    tracks = pd.read_csv(tracks_csv)
    sources = sorted(set(tracks["source"])) if "source" in tracks else ["unknown"]
    res = iceberg.evaluate_constant_velocity(tracks)
    return {"baseline": "constant_velocity", "tracks_file": str(tracks_csv),
            "tracks_source": sources, "n_bergs": int(tracks["berg_id"].nunique()),
            "n_fixes": len(tracks), "horizons": res}


def _routing_report(store: xr.Dataset, day_index: int = 0) -> dict:
    r = routing.baseline_route_from_store(store, day_index, BHARATI, MAITRI)
    day = str(pd.Timestamp(store["time"].values[day_index]).date())
    return {"baseline": "shortest_path", "date": day,
            "from": {"name": "Bharati", "lat": BHARATI[0], "lon": BHARATI[1]},
            "to": {"name": "Maitri", "lat": MAITRI[0], "lon": MAITRI[1]},
            "result": r}


def run_baselines(store_path: Path = DEFAULT_STORE,
                  tracks_csv: Path = DEFAULT_TRACKS,
                  out_dir: Path = DEFAULT_OUT,
                  routing_day: int = 0) -> dict:
    store = xr.open_dataset(store_path, engine="h5netcdf")
    sic = store["sic"].values.astype(float)

    sic_report = sea_ice.evaluate_persistence(sic)
    report = {
        "phase": 5,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feature_store": str(store_path),
        "feature_store_time_range": [str(pd.Timestamp(store["time"].values[0]).date()),
                                     str(pd.Timestamp(store["time"].values[-1]).date())],
        "grid": {"epsg": 3412, "spacing_km": 25.0, "ny": store.sizes["y"],
                 "nx": store.sizes["x"]},
        "sea_ice": {"baseline": "persistence", "sic_units": "fraction",
                    "horizons": sic_report},
        "iceberg": _iceberg_report(tracks_csv),
        "routing": _routing_report(store, day_index=routing_day),
    }
    store.close()

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"baselines_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    # also write a stable "latest" pointer for other tools/UI
    latest = out_dir / "latest.json"
    latest.write_text(out_path.read_text(encoding="utf-8"), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Phase 5 baselines evaluation")
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--tracks", default=str(DEFAULT_TRACKS))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--routing-day", type=int, default=0)
    args = ap.parse_args(argv)
    report = run_baselines(Path(args.store), Path(args.tracks), Path(args.out),
                           routing_day=args.routing_day)
    _print_report(report)


def _print_report(report: dict) -> None:
    print("=" * 60)
    print("PHASE 5 BASELINES — RECORDED RUN")
    print("=" * 60)
    print(f"feature store: {report['feature_store']}")
    print(f"time range:    {report['feature_store_time_range']}")
    print()
    print("--- Sea-ice persistence (FR-6) ---")
    for h, m in report["sea_ice"]["horizons"].items():
        print(f"  h={h:>2}d  MAE={m['mae']:.4f}  RMSE={m['rmse']:.4f}  (n_pairs={m['n_pairs']})")
    print()
    print("--- Iceberg constant-velocity (FR-9) ---")
    ib = report["iceberg"]
    print(f"  tracks: {ib['tracks_file']} (source={ib['tracks_source']}, "
          f"{ib['n_bergs']} bergs, {ib['n_fixes']} fixes)")
    for h, m in ib["horizons"].items():
        if m.get("n", 0):
            print(f"  h={h:>3d}h  mean err={m['mean_km']:.2f} km  "
                  f"median={m.get('median_km', float('nan')):.2f} km  (n={m['n']})")
        else:
            print(f"  h={h:>3d}h  no evaluation samples (tracks too short)")
    print()
    print("--- Shortest-path routing (FR-21) ---")
    rt = report["routing"]["result"]
    if rt["found"]:
        print(f"  date: {report['routing']['date']}  from Bharati to Maitri")
        print(f"  distance: {rt['distance_km']:.0f} km over {rt['n_cells']} cells")
    else:
        print(f"  NO ROUTE: {rt.get('reason')}")
    print(f"\nreport: {report['created_utc']}")


if __name__ == "__main__":
    main()
