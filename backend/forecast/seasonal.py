"""Phase 6 (multi-season) — seasonal SIC forecast model.

Why: a single summer window cannot separate the seasonal signal from noise,
so the Phase 3 OSI SAF CDR record (2002-2020) is used to learn the seasonal
evolution of SIC. The model here is deliberately simple and explainable:

    forecast[t+h] = sic[t] + sum over days d=t..t+h-1 of
                    seasonal_change(cell, d)

where seasonal_change(cell, d) is the mean over TRAINING seasons of
sic(d+1)-sic(d) at the same day-in-season (smoothed across neighbouring
days to reduce single-season noise). Persistence is the delta=0 special
case; a climatological melt signal adds skill only where it is real.

Evaluation: the demo window (2019-12-01..2020-03-15) is EXCLUDED from
training (the builder drops it) and serves as the held-out season. We report
model vs persistence over the later fraction of the held-out window,
comparable to the Phase 6 ridge evaluation.
"""
from __future__ import annotations

import numpy as np


def seasonal_change_map(train_sic: np.ndarray, season_len: int,
                        window_half: int = 5) -> np.ndarray:
    """Expected daily SIC change per cell and day-in-season from training seasons.

    train_sic: (T_train, ny, nx) concatenated aligned training seasons.
    season_len: days per season.
    Returns chg (ny, nx, season_len-1): mean smoothed change from day d to d+1.
    """
    T = train_sic.shape[0]
    n_seasons = T // season_len
    if n_seasons < 2:
        raise ValueError("need >= 2 training seasons for a climatology")
    ny, nx = train_sic.shape[1], train_sic.shape[2]
    s = train_sic[: n_seasons * season_len].reshape(n_seasons, season_len, ny, nx)
    dchg = np.diff(s, axis=1)  # (n_seasons, season_len-1, ny, nx)

    # smooth along the phase (day-in-season) axis: moving mean over
    # 2*window_half+1 neighbouring days, NaN-aware, fully vectorized
    w = 2 * window_half + 1
    padded = np.pad(dchg, ((0, 0), (window_half, window_half), (0, 0), (0, 0)),
                    mode="edge")
    clean = np.where(np.isnan(padded), 0.0, padded)
    # zero-prefixed cumsum so window sums keep the full length (n - w + 1)
    csum = np.concatenate([np.zeros_like(clean[:, :1]), np.cumsum(clean, axis=1)],
                          axis=1)
    cvalid = np.concatenate([np.zeros_like(padded[:, :1]).astype(int),
                             np.cumsum(~np.isnan(padded), axis=1)], axis=1)
    sums = csum[:, w:, :, :] - csum[:, :-w, :, :]
    cnts = cvalid[:, w:, :, :] - cvalid[:, :-w, :, :]
    smoothed = np.where(cnts > 0, sums / np.maximum(cnts, 1), np.nan)
    # mean over seasons, NaN-safe and warning-free (cells with no data stay NaN)
    valid = ~np.isnan(smoothed)
    ssum = np.where(valid, smoothed, 0.0).sum(axis=0)
    scnt = valid.sum(axis=0)
    chg = np.where(scnt > 0, ssum / np.maximum(scnt, 1), np.nan)  # (season_len-1, ny, nx)
    return np.transpose(chg, (1, 2, 0))  # (ny, nx, season_len-1)


def forecast_from_map(chg_cell: np.ndarray, phase: int, horizon: int) -> float:
    """Summed expected change from day `phase` over `horizon` days."""
    end = min(phase + horizon, len(chg_cell))
    return float(np.sum(chg_cell[phase:end]))


def evaluate_seasonal(train_sic: np.ndarray, test_sic: np.ndarray,
                      season_len: int, split_frac: float = 0.7,
                      horizons: tuple[int, ...] = (1, 2, 3, 4, 5),
                      window_half: int = 5,
                      min_valid_days: int = 60) -> dict:
    """Seasonal-climatology model vs persistence on a held-out season.

    train_sic: concatenated aligned training seasons (T_tr, ny, nx).
    test_sic: (T_te, ny, nx) one season; its later (1-split_frac) is scored.
    Only cells observed on enough days are scored (noise guard).
    """
    chg = seasonal_change_map(train_sic, season_len, window_half=window_half)
    ny, nx, L = chg.shape  # L = season_len - 1
    T_te = test_sic.shape[0]
    n_start = int(T_te * split_frac)

    cells_valid = np.isfinite(test_sic).sum(axis=0) >= min_valid_days
    ys, xs = np.where(cells_valid)

    out: dict = {}
    for h in horizons:
        if T_te - n_start - h < 5:
            continue
        model_err = np.zeros((T_te - n_start - h, len(ys)))
        pers_err = np.zeros_like(model_err)
        for ti in range(T_te - n_start - h):
            t = n_start + ti
            phase = t  # day-in-season index (aligned seasons start day 0)
            if phase >= L:
                break
            s_now = test_sic[t, ys, xs]
            truth = test_sic[t + h, ys, xs]
            # expected change summed over [phase, phase+h)
            pred_shift = np.sum(chg[ys, xs, phase:phase + h], axis=1)
            pred = np.clip(s_now + pred_shift, 0.0, 1.0)
            ok = np.isfinite(s_now) & np.isfinite(truth)
            model_err[ti] = np.where(ok, np.abs(truth - pred), np.nan)
            pers_err[ti] = np.where(ok, np.abs(truth - s_now), np.nan)
        model_err = model_err[np.isfinite(model_err)]
        pers_err = pers_err[np.isfinite(pers_err)]
        if len(model_err) == 0:
            continue
        out[int(h)] = {
            "seasonal_mae": float(np.mean(model_err)),
            "seasonal_rmse": float(np.sqrt(np.mean(model_err ** 2))),
            "persistence_mae": float(np.mean(pers_err)),
            "persistence_rmse": float(np.sqrt(np.mean(pers_err ** 2))),
            "n_pairs": int(len(model_err)),
            "improvement_rmse": float(np.sqrt(np.mean(pers_err ** 2))
                                      - np.sqrt(np.mean(model_err ** 2))),
            "note": "positive improvement_rmse means the seasonal model beats "
                    "persistence on RMSE",
        }
    return out
