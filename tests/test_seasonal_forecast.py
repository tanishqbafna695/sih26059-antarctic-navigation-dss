"""Phase 6 (multi-season) tests: seasonal-climatology SIC model (FR-5/6)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from backend.forecast import seasonal as m


def _season_with_trend(n_seasons=3, season_len=60, ny=10, nx=10,
                       seed=3, noise=0.004):
    """Each season: cells decline linearly through the season (a learnable
    seasonal signal shared across seasons), plus noise. Later half of the last
    season is the held-out scoring window."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, season_len)
    out = np.empty((n_seasons * season_len, ny, nx))
    for s in range(n_seasons):
        for yi in range(ny):
            for xi in range(nx):
                start = rng.uniform(0.5, 0.95)
                rate = rng.uniform(0.2, 0.5)  # all cells retreat every season
                out[s * season_len:(s + 1) * season_len, yi, xi] = \
                    np.clip(start - rate * t, 0.02, 0.98)
    out = np.clip(out + rng.normal(0, noise, out.shape), 0.0, 1.0)
    return out


def test_seasonal_change_map_shape_and_alignment():
    train = _season_with_trend(n_seasons=3, season_len=60)
    chg = m.seasonal_change_map(train, 60)
    assert chg.shape == (10, 10, 59)  # (ny, nx, season_len-1)
    # all cells retreat: mean change must be negative
    assert np.nanmean(chg) < -1e-4


def test_seasonal_change_map_rejects_single_season():
    with pytest.raises(ValueError):
        m.seasonal_change_map(np.zeros((60, 4, 4)), 60)


def test_smoothing_is_nan_safe():
    train = _season_with_trend(n_seasons=3, season_len=60)
    # knock out a few cells entirely (outside-coverage pattern from real data)
    train[:, 0, 0] = np.nan
    chg = m.seasonal_change_map(train, 60)
    assert np.isnan(chg[0, 0]).all()  # never-observed cell stays NaN
    assert np.isfinite(chg[5, 5]).all()


def test_seasonal_beats_persistence_on_learnable_signal():
    train = _season_with_trend(n_seasons=4, season_len=60, ny=12, nx=12)
    # held-out season with the SAME seasonal retreat pattern
    test = _season_with_trend(n_seasons=1, season_len=60, ny=12, nx=12, seed=9)
    res = m.evaluate_seasonal(train, test, 60, split_frac=0.5,
                              horizons=(3, 5), min_valid_days=20)
    # the climatology knows the retreat; persistence does not
    assert res[3]["improvement_rmse"] > 1e-5
    assert res[5]["improvement_rmse"] > 1e-5


def test_no_improvement_claimed_on_static_field():
    # static field: persistence is perfect; model must not claim a win
    train = np.tile(np.linspace(0.3, 0.7, 8).reshape(1, 1, 8),
                    (3 * 60, 8, 1)).reshape(3, 60, 8, 8).transpose(1, 0, 2, 3)
    train = np.broadcast_to(np.full((60, 3, 8, 8), 0.5), (60, 3, 8, 8)).copy()
    train = train.reshape(180, 8, 8)
    test = np.full((60, 8, 8), 0.5)
    res = m.evaluate_seasonal(train, test, 60, split_frac=0.5,
                              horizons=(2,), min_valid_days=20)
    assert res[2]["persistence_rmse"] == pytest.approx(0.0, abs=1e-9)
    assert res[2]["improvement_rmse"] < 1e-6


def test_end_to_end_on_real_training_and_store():
    tp = Path("data/processed/training_sic_seasons.nc")
    sp = Path("data/processed/bharati_maitri_2019_20/features.nc")
    if not (tp.exists() and sp.exists()):
        pytest.skip("real training/store not present (run the data pipeline first)")
    from backend.forecast.evaluate_seasonal import run_evaluation
    report = run_evaluation(train_path=tp, store_path=sp)
    assert "seasonal_rmse" in report["horizons"]["1"]
    assert "persistence_rmse" in report["horizons"]["1"]
    assert report["horizons"]["1"]["n_pairs"] > 100_000
    assert report["model"].startswith("seasonal-climatology")
