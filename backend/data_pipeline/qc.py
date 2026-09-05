"""Validation / QC: range checks, missing-data rates, flags (brief §23, §45)."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np


@dataclass
class QCReport:
    product: str
    n_values: int = 0
    missing_rate: float = 0.0
    out_of_range_rate: float = 0.0
    flags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def missing_rate(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return 0.0
    return float(np.isnan(arr).mean())


def range_failure_rate(values: np.ndarray, vmin: float | None, vmax: float | None) -> float:
    arr = np.asarray(values, dtype=float)
    if arr.size == 0 or (vmin is None and vmax is None):
        return 0.0
    bad = np.zeros(arr.shape, dtype=bool)
    if vmin is not None:
        bad |= arr < vmin
    if vmax is not None:
        bad |= arr > vmax
    valid = ~np.isnan(arr)
    return float(bad[valid].mean()) if valid.any() else 0.0


def run_qc(name: str, values: np.ndarray, vmin: float | None = None,
           vmax: float | None = None, flags: list | None = None) -> QCReport:
    arr = np.asarray(values, dtype=float)
    return QCReport(
        product=name,
        n_values=int(np.prod(arr.shape)),
        missing_rate=missing_rate(arr),
        out_of_range_rate=range_failure_rate(arr, vmin, vmax),
        flags=list(flags or []),
    )