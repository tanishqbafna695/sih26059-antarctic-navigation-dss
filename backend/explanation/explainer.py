"""Template-based route explanation (FR-27 recommendation, FR-28 change).

Honesty rules enforced in code:
- Every claim cites a recorded number (delta %, limit, confidence label).
- Strengths must pass a significance bar (|pct| >= 1.0 AND, for hazard/
  exposure metrics, absolute difference >= 0.002) so noise like
  "50% less iceberg risk" on 0.0002-vs-0.0001 is never uttered.
- Costs are always shown alongside gains: a winner that is slower says so,
  or earns an explicit "negligible extra cost" note. Never one-sided.
- No-route input yields an honest no-explanation statement, never prose
  about a route that does not exist.
- FR-28 change explanations take an explicit human-supplied trigger string
  (e.g. "new iceberg fix 40 km ahead"); the engine reports WHAT changed and
  by how much, it never invents WHY the environment changed.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

METRIC_WORDS = {
    "travel_time_h": "travel time",
    "fuel_liters": "fuel use",
    "mean_hazard": "predicted risk",
    "ice_exposure_frac": "ice exposure",
    "mean_iceberg_hazard": "iceberg risk",
}

MENTION_PCT = 1.0       # relative bar for mentioning any delta
ABS_GUARD = 0.002       # absolute bar for hazard/exposure deltas (noise cut)
GUARDED = ("mean_hazard", "ice_exposure_frac", "mean_iceberg_hazard")

PROTOTYPE_LINE = ("Research prototype decision support: modeled risk, never "
                  "a guarantee of safe navigation.")


def _fmt_val(metric: str, v: float) -> str:
    if metric == "travel_time_h":
        return f"{v:.1f} h"
    if metric == "fuel_liters":
        return f"{v:,.0f} L"
    if metric in ("ice_exposure_frac",):
        return f"{v * 100:.1f}% of path"
    return f"{v:.3f}"


def _significant(metric: str, delta_pct: float, abs_diff: float) -> bool:
    if abs(delta_pct) < MENTION_PCT:
        return False
    if metric in GUARDED and abs_diff < ABS_GUARD:
        return False
    return True


def explain_recommendation(rows: List[Dict[str, Any]],
                           recommendation: Dict[str, Any],
                           vessel: Dict[str, Any]) -> Dict[str, Any]:
    """Explain a recommendation from comparison rows + deltas + vessel limits.

    rows: comparison rows (must include the winner). recommendation: Phase 13
    recommend() output. vessel: {name, ice_class, max_sic_limit} (fractions).
    """
    winner = recommendation.get("recommended")
    if winner is None:
        return {"explained": False,
                "reason": recommendation.get("reason", "no route to explain"),
                "text": "No route to explain: "
                        f"{recommendation.get('reason', 'no route available')}."}
    by_name = {r["route"]: r for r in rows}
    wrow = by_name[winner]
    profile = recommendation.get("profile", "balanced")

    strengths: List[str] = []
    prices: List[str] = []
    for alt, dd in recommendation.get("deltas_vs_alternatives_pct", {}).items():
        for metric, d in dd.items():
            if d is None:
                continue
            word = METRIC_WORDS.get(metric, metric)
            wv = float(wrow[metric])
            av = float(by_name[alt][metric])
            if d < 0 and _significant(metric, d, abs(wv - av)):
                strengths.append(
                    f"{abs(d):.1f}% less {word} than the {alt} route "
                    f"({_fmt_val(metric, wv)} vs {_fmt_val(metric, av)})")
            elif d > 0 and abs(d) >= MENTION_PCT:
                prices.append(
                    f"{d:.1f}% more {word} than the {alt} route "
                    f"({_fmt_val(metric, wv)} vs {_fmt_val(metric, av)})")
    # de-duplicate while preserving order
    strengths = list(dict.fromkeys(strengths))
    prices = list(dict.fromkeys(prices))
    if not prices:
        prices.append("extra time/fuel cost is negligible (all within 1%)")

    ice_pct = float(wrow["ice_exposure_frac"]) * 100.0
    limit_pct = float(vessel.get("max_sic_limit", 1.0)) * 100.0
    vessel_statement = (
        f"{vessel.get('name', 'Vessel')} ({vessel.get('ice_class', 'unknown class')}): "
        f"advised path averages {ice_pct:.1f}% ice-covered waters against a "
        f"{limit_pct:.0f}% operating limit; worst modeled cell hazard "
        f"{float(wrow['max_hazard']):.3f} (blocking threshold 1.0 -- violated "
        f"cells are excluded by construction, never crossed)")

    conf_rows = rows[0] if rows else {}
    confidence_note = (
        f"Route-set confidence {float(wrow.get('confidence', float('nan'))):.2f} "
        f"({wrow.get('confidence_label', 'UNKNOWN')}) -- shared across all three "
        f"options, not per-route precision")
    caveats = list(recommendation.get("caveats", []))

    gist = (f"Take the {winner} route: {wrow['travel_time_h']:.1f} h, "
            f"{wrow['fuel_liters']:,.0f} L, predicted risk {wrow['mean_hazard']:.3f} "
            f"(chosen under {profile} priorities)")
    lines = [gist, ""]
    lines.append("Why this route:")
    lines += [f"- {s}" for s in strengths] or ["- (no significant advantage found)"]
    lines.append("The price of this choice:")
    lines += [f"- {p}" for p in prices]
    lines += ["", f"Vessel fit: {vessel_statement}", "",
              f"Confidence: {confidence_note}"]
    lines += [f"- Caveat: {c}" for c in caveats]
    lines += ["", PROTOTYPE_LINE]
    return {
        "explained": True,
        "winner": winner,
        "profile": profile,
        "headline": gist,
        "strengths": strengths,
        "prices": prices,
        "vessel_statement": vessel_statement,
        "confidence_note": confidence_note,
        "caveats": caveats,
        "text": "\n".join(lines),
    }


def explain_change(old: Dict[str, Any], new: Dict[str, Any],
                   trigger: str) -> Dict[str, Any]:
    """Explain a recommendation update given old/new winner summaries (FR-28).

    old/new: {recommended, travel_time_h, fuel_liters, mean_hazard} for the
    previously and currently advised routes. trigger: human-supplied
    description of the environmental change (never invented here).
    Phase 15 feeds real re-route pairs; Phase 14 validates the logic on
    recorded-shape synthetic pairs.
    """
    ow, nw = old.get("recommended"), new.get("recommended")
    if ow is None or nw is None:
        return {"explained": False,
                "reason": "one side of the change has no route",
                "text": "Cannot explain the change: one side has no route."}
    # parenthetical qualifiers (e.g. "safest (remaining course)") do not make
    # it a different route: compare base names for switch detection.
    def _base(s: str) -> str:
        return str(s).split(" (")[0]
    switched = _base(ow) != _base(nw)
    deltas = {}
    for m in ("travel_time_h", "fuel_liters", "mean_hazard"):
        a, b = float(old[m]), float(new[m])
        deltas[m] = None if a == 0 else round((b - a) / abs(a) * 100.0, 1)
    if not switched:
        headline = (f"Recommendation holds: {nw} remains advised after "
                    f"{trigger}")
    else:
        headline = (f"Recommendation changed: {ow} -> {nw} after {trigger}")
    parts = [headline]
    for m in ("travel_time_h", "fuel_liters", "mean_hazard"):
        d = deltas[m]
        if d is None:
            continue
        direction = "higher" if d > 0 else "lower"
        parts.append(f"- {METRIC_WORDS[m]} {direction} by {abs(d):.1f}% "
                     f"({old[m]} -> {new[m]})")
    parts += ["", PROTOTYPE_LINE]
    return {
        "explained": True,
        "old_winner": ow,
        "new_winner": nw,
        "switched": switched,
        "trigger": trigger,
        "deltas_pct": deltas,
        "headline": headline,
        "text": "\n".join(parts),
    }
