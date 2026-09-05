"""Phase 6 tests: delta-ridge SIC forecast model (FR-5), uncertainty sigma
(FR-7), temporal-split evaluation vs persistence (FR-6)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from backend.forecast import sea_ice as m


def _retreating_field(T=150, ny=20, nx=20, seed=1, noise=0.005):
    """Per-cell smooth linear decline persisting across the whole window: a
    trend (learnable signal) present in both train and held-out parts.
    NOTE: threshold-edge fields (flat then abrupt drop) are NOT used here -
    they defeat any linear-trend model by construction and are recorded as a
    real finding on the actual data (Phase 6 gate log)."""
    t = np.linspace(0.0, 1.0, T)
    rng = np.random.default_rng(seed)
    sic = np.empty((T, ny, nx))
    for yi in range(ny):
        for xi in range(nx):
            start = rng.uniform(0.4, 0.9)
            rate = rng.uniform(0.3, 0.6)
            sic[:, yi, xi] = np.clip(start - rate * t, 0.02, 0.98)
    sic = np.clip(sic + rng.normal(0, noise, sic.shape), 0.0, 1.0)
    return sic


def test_valid_cell_mask():
    sic = np.full((50, 4, 4), np.nan)
    sic[:, 0, 0] = 0.5  # only this cell has data
    msk = m._valid_cell_mask(sic, min_valid=40)
    assert msk.sum() == 1 and msk[0, 0]


def test_fit_predict_delta_consistent_shapes():
    s = np.linspace(1.0, 0.0, 100)  # slow linear retreat
    trend = np.linspace(0.0, 1.0, 100)
    delta = np.diff(s, prepend=s[0])  # constant negative change
    model, resid_std = m.fit_cell_delta_model(s[:80], delta[:80], trend[:80], alpha=0.05)
    assert model is not None
    pd_ = m.predict_delta(model, s, trend)
    assert pd_.shape == s.shape


def test_delta_model_beats_persistence_when_trend_is_real():
    sic = _retreating_field()
    res = m.evaluate_window(sic, split_frac=0.7, horizons=(1, 3, 5), alpha=0.05)
    # on a strong linear retreat the delta model (which learns the trend) must
    # beat persistence at the longer horizons where persistence is most wrong
    assert res[3]["improvement_rmse"] > 0
    assert res[5]["improvement_rmse"] > 0


def test_no_improvement_claimed_on_static_field():
    # constant field: persistence is perfect; the model must not claim a win
    sic = np.tile(np.linspace(0.2, 0.8, 8).reshape(1, 1, 8), (120, 10, 1))
    sic = np.broadcast_to(sic, (120, 10, 8)).copy()
    res = m.evaluate_window(sic, split_frac=0.7, horizons=(1, 3), alpha=0.05)
    assert res[1]["persistence_rmse"] == pytest.approx(0.0, abs=1e-9)
    # model may have tiny error but must not be meaningfully better
    assert res[1]["improvement_rmse"] < 1e-6


def test_uncertainty_sigma_reported():
    sic = _retreating_field(noise=0.02)
    res = m.evaluate_window(sic, split_frac=0.7, horizons=(2,), alpha=0.05)
    assert np.isfinite(res[2]["sigma_mean"])
    assert res[2]["sigma_mean"] > 0


def test_temporal_split_no_shuffle():
    sic = _retreating_field()
    T = sic.shape[0]
    n_train = int(0.7 * T)
    res = m.evaluate_window(sic, split_frac=0.7, horizons=(2,), alpha=0.05)
    # n_pairs must equal (cells) * (T - n_train - h) roughly; it is strictly the
    # held-out later pairs, never shuffled training data
    assert res[2]["n_pairs"] > 0
    assert res[2]["n_pairs"] < 0.5 * sic.shape[1] * sic.shape[2] * T  # not the whole series


def test_end_to_end_on_real_feature_store():
    p = Path("data/processed/bharati_maitri_2019_20/features.nc")
    if not p.exists():
        pytest.skip("real feature store not present (run the data pipeline first)")
    import xarray as xr
    from backend.forecast.evaluate_sea_ice import run_evaluation
    report = run_evaluation(store_path=p)
    h1 = report["horizons"]["1"]
    assert "ridge_mae" in h1 and "persistence_rmse" in h1
    assert h1["n_pairs"] > 100_000
    assert "uncertainty" in report
