"""Phase 6 (multi-season) evaluation: seasonal-climatology SIC forecast vs
persistence on the held-out 2019-20 season (FR-5/6/7).

The seasonal model trains ONLY on prior Dec-Mar seasons (OSI SAF CDR record)
and scores the SAME later fraction of the held-out 2019-20 season that the
Phase 6 ridge evaluation used, so the three numbers (ridge, seasonal,
persistence) are directly comparable on identical (cell, time) pairs.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import xarray as xr

from ..data_pipeline.config import ROOT
from . import seasonal as model

DEFAULT_TRAIN = ROOT / "data" / "processed" / "training_sic_seasons.nc"
DEFAULT_STORE = ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"
DEFAULT_OUT = ROOT / "data" / "forecast"


def run_evaluation(train_path: Path = DEFAULT_TRAIN, store_path: Path = DEFAULT_STORE,
                   out_dir: Path = DEFAULT_OUT, split_frac: float = 0.7,
                   horizons=(1, 2, 3, 4, 5), window_half: int = 5,
                   min_valid_days: int = 60) -> dict:
    train = xr.open_dataset(train_path, engine="h5netcdf")
    train_sic = train["sic"].values.astype(float)
    n_train_days = train_sic.shape[0]
    # per-season length = modal run of consecutive daily steps (seasons are
    # concatenated with multi-day gaps between them)
    t_ord = np.asarray(train["time"].values, dtype="datetime64[D]").astype("int64")
    train.close()
    gaps = np.diff(t_ord)
    run_len = 1
    season_len = 1
    for g in gaps:
        if g == 1:
            run_len += 1
        else:
            season_len = max(season_len, run_len)
            run_len = 1
    season_len = max(season_len, run_len)
    n_seasons = n_train_days // season_len

    store = xr.open_dataset(store_path, engine="h5netcdf")
    test_sic = store["sic"].values.astype(float)
    time_range = [str(store["time"].values[0])[:10], str(store["time"].values[-1])[:10]]
    store.close()

    horizons = tuple(int(h) for h in horizons)
    if n_seasons < 2:
        raise ValueError(f"need >= 2 training seasons for a climatology, "
                         f"found {n_seasons} in {train_path}")
    results = model.evaluate_seasonal(
        train_sic, test_sic, season_len, split_frac=split_frac,
        horizons=horizons, window_half=window_half,
        min_valid_days=min_valid_days)

    report = {
        "phase": 6,
        "model": "seasonal-climatology delta (mean day-in-season change over "
                 f"{n_seasons} prior training seasons)",
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "training_data": str(train_path),
        "training_coverage": "prior Dec-Mar seasons (2019-20 excluded)",
        "feature_store": str(store_path),
        "held_out_season": time_range,
        "split": {"scored_frac": 1 - split_frac,
                  "note": "later fraction of held-out season; identical pairs "
                          "to the Phase 6 ridge evaluation"},
        "sic_units": "fraction",
        "uncertainty": "none (climatology mean; FR-7 sigma stays with ridge/Phase 9)",
        "horizons": {str(h): v for h, v in sorted(results.items())},
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"seasonal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    (out_dir / "latest_seasonal.json").write_text(out_path.read_text(encoding="utf-8"))
    return report


def main(argv: list[str] | None = None) -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Phase 6 seasonal SIC forecast evaluation")
    ap.add_argument("--train", default=str(DEFAULT_TRAIN))
    ap.add_argument("--store", default=str(DEFAULT_STORE))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--split-frac", type=float, default=0.7)
    args = ap.parse_args(argv)
    report = run_evaluation(Path(args.train), Path(args.store), Path(args.out),
                            split_frac=args.split_frac)
    _print(report)


def _print(report: dict) -> None:
    print("=" * 68)
    print("PHASE 6 SEASONAL SIC FORECAST — climatology vs persistence")
    print("=" * 68)
    print(f"train: {report['training_data']}")
    print(f"held-out season: {report['held_out_season']}")
    print()
    print(f"{'h':>3} {'seas MAE':>10} {'seas RMSE':>10} {'pers MAE':>10} "
          f"{'pers RMSE':>10} {'win(RMSE)':>9} {'pairs':>7}")
    for h, r in report["horizons"].items():
        win = r["improvement_rmse"]
        flag = "SEASONAL" if win > 1e-6 else ("persistence" if win < -1e-6 else "tie")
        print(f"{int(h):>3} {r['seasonal_mae']:10.4f} {r['seasonal_rmse']:10.4f} "
              f"{r['persistence_mae']:10.4f} {r['persistence_rmse']:10.4f} "
              f"{win:9.4f} {r['n_pairs']:>7}   {flag}")
    print()
    print(f"report: {report['created_utc']} (data/forecast/latest_seasonal.json)")


if __name__ == "__main__":
    main()
