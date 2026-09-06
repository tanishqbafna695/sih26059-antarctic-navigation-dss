"""Phase 16 — Backtesting (SC-1…SC-8 acceptance evidence).

Runs the recorded full chain over departure-day × vessel matrices and
failure-scenario cases, aggregating success rates, vessel-difference
evidence (SC-6) and no-route records (SC-7). Scenario runs (stale outage,
storm days) live in scripts/backtest/; this package holds the reusable,
unit-tested matrix logic.
"""

from .harness import run_departure_matrix, summarize_matrix

__all__ = [
    "run_departure_matrix",
    "summarize_matrix",
]
