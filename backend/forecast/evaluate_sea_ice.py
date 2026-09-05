"""Phase 6 evaluation: ridge SIC forecast vs persistence on the real store.

Produces a reproducible JSON report under data/forecast/ comparing the ridge
model and the persistence baseline on an identical held-out temporal split
(FR-5/6), plus the residual-based 1-sigma uncertainty (FR-7).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import xarray as xr

from ..data_pipeline.config import ROOT
from . import sea_ice as model

DEFAULT_STORE = ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"
DEFAULT_OUT = ROOT / "data" / "forecast"


def run_evaluation(store_path: Path = DEFAULT_STORE, out_dir: Path = DEFAULT_OUT,
                   split_frac: float = 0.7, horizons=(1, 2, 3, 4, 5),
                   alpha: float = 0.5, min_valid: int = 60) -> dict:
    store = xr.open_dataset(store_path, engine="h5netcdf")
    sic = store["sic"].values.astype(float)
    time_range = [str(store["time"].values[0])[:10], str(store["time"].values[-1])[:10]]
    store.close()

    horizons = tuple(int(h) for h in horizons)
    results = model.evaluate_window(sic, split_frac=split_frac, horizons=horizons,
                                    alpha=alpha, min_valid=min_valid)

    report = {
        "phase": 6,
        "model": "per-cell ridge AR(2)+trend (classical ML, Phase 0 §41 baseline+1)",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feature_store": str(store_path),
        "time_range": time_range,
        "split": {"train_frac": split_frac, "held_out": "later window only (temporal, no shuffle)"},
        "sic_units": "fraction",
        "uncertainty": "residual 1-sigma per cell and horizon (MVP; Phase 9 refines)",
        "horizons": {str(h): v for h, v in sorted(results.items())},
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"sea_ice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    (out_dir / "latest.json").write_text(out_path.read_text(encoding="utf-8"))
    return report


def main(argv: list[str] | None = None) -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Phase 6 sea-ice forecast evaluation")
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--split-frac", type=float, default=0.7)
    ap.add_argument("--alpha", type=float, default=0.5)
    args = ap.parse_args(argv)
    report = run_evaluation(Path(args.store), Path(args.out),
                            split_frac=args.split_frac, alpha=args.alpha)
    _print(report)


def _print(report: dict) -> None:
    print("=" * 68)
    print("PHASE 6 SEA-ICE FORECAST — RIDGE vs PERSISTENCE (held-out later window)")
    print("=" * 68)
    print(f"store: {report['feature_store']}  window: {report['time_range']}")
    print(f"split: train {report['split']['train_frac']:.0%}  ->  test later "
          f"{1 - report['split']['train_frac']:.0%} (no shuffle)")
    print()
    print(f"{'h':>3} {'ridge MAE':>10} {'ridge RMSE':>10} {'pers MAE':>10} "
          f"{'pers RMSE':>10} {'win(RMSE)':>9} {'pairs':>7} {'sigma':>7}")
    for h, r in report["horizons"].items():
        win = r["improvement_rmse"]
        flag = "RIDGE" if win > 1e-6 else ("persistence" if win < -1e-6 else "tie")
        print(f"{int(h):>3} {r['ridge_mae']:10.4f} {r['ridge_rmse']:10.4f} "
              f"{r['persistence_mae']:10.4f} {r['persistence_rmse']:10.4f} "
              f"{win:9.4f} {r['n_pairs']:>7} {r['sigma_mean']:7.4f}   {flag}")
    print()
    print(f"report: {report['created_utc']} (data/forecast/latest.json)")


if __name__ == "__main__":
    main()
