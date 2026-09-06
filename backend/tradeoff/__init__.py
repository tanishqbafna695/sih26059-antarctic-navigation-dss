"""Phase 13 — Route Trade-Off Engine (FR-25, FR-26).

Compares the Fastest / Safest / Balanced routes (+ shortest-path baseline
where available) on time, fuel, risk, ice/iceberg exposure and confidence,
and recommends one route under a named navigator priority profile, with
quantitative %-deltas versus every alternative as the evidence base for the
Phase 14 explanation engine.
"""

from .comparison import build_comparison
from .recommend import PRIORITY_PROFILES, recommend

__all__ = [
    "build_comparison",
    "PRIORITY_PROFILES",
    "recommend",
]
