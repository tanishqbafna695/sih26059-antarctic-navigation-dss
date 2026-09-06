"""Priority-weighted route recommendation (FR-26, Phase 13).

A named navigator priority profile scores the compared routes and selects
one winner. Scoring is min-max normalization per metric across the CANDIDATE
routes (the three multi-objective routes; the baseline is evidence, never a
candidate), weighted sum, lowest score wins. All scored metrics are
lower-is-better (time, fuel, mean hazard, ice exposure, iceberg exposure).

Priority profiles (weights sum to 1.0; documented so the demo can state
exactly what "safety first" means):
- balanced:     risk .40, time .25, fuel .20, ice .10, berg .05 (default)
- safety_first: risk .70, time .10, fuel .10, ice .05, berg .05
- time_first:   risk .10, time .70, fuel .10, ice .05, berg .05
- fuel_saver:   risk .15, time .10, fuel .65, ice .05, berg .05

Tie-break (documented): exact score tie recommends "balanced" — the
middle-ground default — rather than an arbitrary route.

Uncertainty honesty: confidence is NOT a scoring metric (it is set-level).
When the shared confidence label is LOW or DEGRADED the recommendation
carries a caveat string. FR-14 uncertainty-aware re-ranking (risk inflation
inside route costs) is a SHOULD requirement and is NOT wired here; it is
recorded as a caveat, never silently claimed.

Output per recommendation: winner, per-route scores, per-metric %-deltas of
the winner versus EVERY alternative (evidence for Phase 14), structured
quantitative reasons, and caveats. Deltas use (w-a)/|a|*100; a zero baseline
yields null (undefined), never ±inf.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# metric -> profile weight key order used in scoring
SCORE_METRICS = ("mean_hazard", "travel_time_h", "fuel_liters",
                 "ice_exposure_frac", "mean_iceberg_hazard")

PRIORITY_PROFILES: Dict[str, Dict[str, float]] = {
    "balanced": {"mean_hazard": 0.40, "travel_time_h": 0.25,
                 "fuel_liters": 0.20, "ice_exposure_frac": 0.10,
                 "mean_iceberg_hazard": 0.05},
    "safety_first": {"mean_hazard": 0.70, "travel_time_h": 0.10,
                     "fuel_liters": 0.10, "ice_exposure_frac": 0.05,
                     "mean_iceberg_hazard": 0.05},
    "time_first": {"mean_hazard": 0.10, "travel_time_h": 0.70,
                   "fuel_liters": 0.10, "ice_exposure_frac": 0.05,
                   "mean_iceberg_hazard": 0.05},
    "fuel_saver": {"mean_hazard": 0.15, "travel_time_h": 0.10,
                   "fuel_liters": 0.65, "ice_exposure_frac": 0.05,
                   "mean_iceberg_hazard": 0.05},
}

for _name, _w in PRIORITY_PROFILES.items():
    assert abs(sum(_w.values()) - 1.0) < 1e-9, f"profile {_name} weights must sum to 1"

_CANDIDATES = ("fastest", "safest", "balanced")


def _normalize(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Min-max normalize each scored metric across candidate rows to [0,1].

    Zero range (identical values) -> 0.0 for all (no discrimination).
    """
    norm: Dict[str, Dict[str, float]] = {}
    for metric in SCORE_METRICS:
        vals = [float(r[metric]) for r in rows]
        lo, hi = min(vals), max(vals)
        span = hi - lo
        for r in rows:
            norm.setdefault(r["route"], {})[metric] = (
                0.0 if span <= 0 else (float(r[metric]) - lo) / span)
    return norm


def score_routes(rows: List[Dict[str, Any]],
                 profile_weights: Dict[str, float]) -> Dict[str, float]:
    """Weighted-score each row (lower wins). Returns {route: score in [0,1]}."""
    norm = _normalize(rows)
    return {r["route"]: round(sum(profile_weights[m] * norm[r["route"]][m]
                                 for m in SCORE_METRICS), 6)
            for r in rows}


def delta_pct(winner_val: float, alt_val: float) -> Optional[float]:
    """%-delta of winner vs alternative; None when the baseline is zero."""
    w, a = float(winner_val), float(alt_val)
    if a == 0.0:
        return None if w != 0.0 else 0.0
    return round((w - a) / abs(a) * 100.0, 1)


def recommend(comparison: Dict[str, Any],
              profile: str = "balanced") -> Dict[str, Any]:
    """Recommend one route from a comparison table under a priority profile.

    Returns winner + scores + deltas-vs-alternatives + reasons + caveats, or
    {"recommended": None, ...} when no routes exist (FR-24 passthrough).
    """
    if not comparison.get("routes_available"):
        return {"recommended": None,
                "reason": comparison.get("reason", "no routes available"),
                "profile": profile}
    if profile not in PRIORITY_PROFILES:
        raise KeyError(f"unknown priority profile {profile!r}; "
                       f"available: {sorted(PRIORITY_PROFILES)}")
    weights = PRIORITY_PROFILES[profile]
    rows = [r for r in comparison["rows"] if r["route"] in _CANDIDATES]
    if not rows:
        return {"recommended": None, "reason": "no candidate routes",
                "profile": profile}
    scores = score_routes(rows, weights)
    best = min(scores.values())
    tied = sorted([r for r, s in scores.items() if s == best])
    winner = "balanced" if len(tied) > 1 and "balanced" in tied else tied[0]
    wrow = next(r for r in rows if r["route"] == winner)

    # deltas + structured quantitative reasons vs every other candidate
    deltas: Dict[str, Dict[str, Optional[float]]] = {}
    reasons: List[Dict[str, Any]] = []
    for alt in rows:
        if alt["route"] == winner:
            continue
        dd = {m: delta_pct(wrow[m], alt[m]) for m in SCORE_METRICS}
        deltas[alt["route"]] = dd
        for m in SCORE_METRICS:
            d = dd[m]
            if d is None:
                continue
            reasons.append({
                "metric": m,
                "winner_value": float(wrow[m]),
                "vs_route": alt["route"],
                "vs_value": float(alt[m]),
                "delta_pct": d,
                "better": bool(d < 0),
            })
    # headline reasons: the winner's two largest improvements (data for Ph14)
    headline = sorted([r for r in reasons if r["better"]],
                      key=lambda r: r["delta_pct"])[:2]

    caveats: List[str] = []
    conf_label = comparison.get("confidence", {}).get("status_label", "UNKNOWN")
    if conf_label in ("LOW", "DEGRADED"):
        caveats.append(
            f"route-set confidence is {conf_label}: recommendation uses mean "
            f"hazard only; FR-14 uncertainty-aware re-ranking is not applied "
            f"in this phase")
    if len(rows) < 3:
        caveats.append("fewer than three candidate routes available")
    if all(s == best for s in scores.values()):
        caveats.append("all candidates score identically under this profile; "
                       "default tie-break selected 'balanced'")

    return {
        "recommended": winner,
        "profile": profile,
        "profile_weights": dict(weights),
        "scores": scores,
        "deltas_vs_alternatives_pct": deltas,
        "reasons": reasons,
        "headline_improvements": headline,
        "caveats": caveats,
        "tied": len(tied) > 1,
    }
