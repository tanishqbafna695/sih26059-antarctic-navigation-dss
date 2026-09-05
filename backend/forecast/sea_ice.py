"""Phase 6 — Sea-ice concentration forecast (FR-5, FR-7).

Model progression (Phase 0 §41): the persistence baseline from Phase 5 is the
bar. The first classical-ML step predicts the SIC *delta* over the horizon,
not the level:

    delta[t, h] = sic[t+h] - sic[t]          (target)
    prediction  = sic[t] + f(features at t)  ->  sic[t+h]

Persistence is the delta=0 special case, so the model can only beat it by
learning when and how much SIC will change. (Predicting the level directly
shrinks the autoregressive coefficient below 1 and loses to persistence on
the near-static majority of cells - a finding recorded in the Phase 6 gate.)

Features per cell are deliberately simple: a constant, the recent SIC change
(sic[t]-sic[t-1]), and a linear time/season trend. Ridge regression per cell
and horizon, alpha small.

Evaluation is a strict temporal split: train on the early window, evaluate on
the LATER held-out window (no shuffling - forecasting never trains on the
future). MAE/RMSE are computed over identical held-out (cell, time) pairs for
model and persistence.

Uncertainty (FR-7): residual 1-sigma per cell and horizon from in-sample fit
errors, reported as a band around each forecast. A calibrated uncertainty
engine arrives in Phase 9.
"""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import Ridge


def _valid_cell_mask(sic: np.ndarray, min_valid: int = 60) -> np.ndarray:
    """Cells with at least min_valid daily observations in the window."""
    return (~np.isnan(sic)).sum(axis=0) >= min_valid


def fit_cell_delta_model(s_t: np.ndarray, delta_target: np.ndarray,
                         trend: np.ndarray, alpha: float = 0.5) -> tuple:
    """Fit ridge for one cell: x=[1, sic[t]-sic[t-1], trend] -> delta[t,h].

    s_t: SIC series at train times t=0..n-1.
    delta_target: sic[t+h]-sic[t] over the same times.
    trend: absolute normalized time (0..1 over the FULL window) so train and
    predict use the same feature scale.
    Returns (model, resid_std).
    """
    n = len(s_t)
    if n < 30:
        return None, np.nan
    change = np.diff(s_t, prepend=s_t[0])  # sic[t]-sic[t-1]
    x = np.stack([np.ones(n), change, np.asarray(trend, dtype=float)], axis=1)
    y = np.asarray(delta_target, dtype=float)
    ok = np.isfinite(y) & np.isfinite(change) & np.isfinite(x).all(axis=1)
    if ok.sum() < 30:
        return None, np.nan
    model = Ridge(alpha=alpha).fit(x[ok], y[ok])
    resid = y[ok] - model.predict(x[ok])
    resid_std = float(np.std(resid, ddof=1)) if len(resid) > 1 else np.nan
    return model, resid_std


def predict_delta(model, s_t: np.ndarray, trend: np.ndarray) -> np.ndarray:
    """Predict delta for every time index t of a cell series s_t."""
    change = np.diff(s_t, prepend=s_t[0])
    x = np.stack([np.ones(len(s_t)), change, np.asarray(trend, dtype=float)], axis=1)
    return model.predict(x)


def evaluate_window(sic: np.ndarray, split_frac: float = 0.7,
                    horizons: tuple[int, ...] = (1, 2, 3, 4, 5),
                    alpha: float = 0.05, min_valid: int = 60) -> dict:
    """Temporal-split evaluation of delta-ridge vs persistence per horizon.

    sic: (T, ny, nx) SIC fractions with NaN outside coverage.
    Returns {horizon: {ridge_mae, ridge_rmse, pers_mae, pers_rmse, n_pairs,
    n_cells, sigma_mean, improvement_rmse}}.
    """
    sic = np.asarray(sic, dtype=float)
    T = sic.shape[0]
    n_train = int(T * split_frac)
    cells = np.argwhere(_valid_cell_mask(sic, min_valid=min_valid))
    trend_full = np.linspace(0.0, 1.0, T)  # absolute scale for train and predict

    out: dict = {}
    for h in horizons:
        if n_train - h < 40 or T - n_train - h < 5:
            continue
        ridge_abs, pers_abs, sigmas = [], [], []
        for y, x in cells:
            s = sic[:, y, x]
            # train pairs t in [0, n_train-h): feature sic[t], target sic[t+h]
            s_train = s[:n_train - h]
            delta_target = s[h:n_train] - s[:n_train - h]
            model, resid_std = fit_cell_delta_model(
                s_train, delta_target, trend_full[:n_train - h], alpha)
            if model is None:
                continue
            pred_delta = predict_delta(model, s, trend_full)
            for t in range(n_train, T - h):
                truth = s[t + h]
                if not np.isfinite(truth) or not np.isfinite(s[t]):
                    continue
                # delta predictions can overshoot the [0,1] SIC domain; clip
                pred = np.clip(s[t] + pred_delta[t], 0.0, 1.0)
                ridge_abs.append(abs(truth - pred))
                pers_abs.append(abs(truth - s[t]))
            if np.isfinite(resid_std):
                sigmas.append(resid_std)
        if not ridge_abs:
            continue
        ridge_abs = np.asarray(ridge_abs)
        pers_abs = np.asarray(pers_abs)
        out[int(h)] = {
            "ridge_mae": float(np.mean(ridge_abs)),
            "ridge_rmse": float(np.sqrt(np.mean(ridge_abs ** 2))),
            "persistence_mae": float(np.mean(pers_abs)),
            "persistence_rmse": float(np.sqrt(np.mean(pers_abs ** 2))),
            "n_pairs": int(len(ridge_abs)),
            "n_cells": int(len(sigmas)),
            "sigma_mean": float(np.mean(sigmas)) if sigmas else np.nan,
            "improvement_rmse": float(np.sqrt(np.mean(pers_abs ** 2))
                                      - np.sqrt(np.mean(ridge_abs ** 2))),
            "note": "positive improvement_rmse means the model beats persistence",
        }
    return out
