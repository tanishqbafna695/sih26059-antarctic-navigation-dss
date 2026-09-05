"""Phase 5 — Mandatory baselines.

Every predictive/routing component must be benchmarked against a documented
baseline before any "improvement" claim is made (Phase 0 §6, C-4; FR-6, FR-9,
FR-21). This package provides:

- sea_ice:   persistence SIC forecast baseline            (FR-6)
- iceberg:   constant-velocity trajectory baseline        (FR-9)
- routing:   shortest-path route baseline                 (FR-21)
- metrics:   shared evaluation metrics (MAE, RMSE, ...)
"""

from . import iceberg, metrics, routing, sea_ice

__all__ = ["metrics", "sea_ice", "iceberg", "routing"]
