"""Phase 13 tests: trade-off comparison (FR-25) + recommendation (FR-26)."""
from __future__ import annotations

import pytest

from backend.tradeoff import PRIORITY_PROFILES, build_comparison, recommend
from backend.tradeoff.comparison import comparison_markdown
from backend.tradeoff.recommend import delta_pct, score_routes


def _route(time_h, fuel, risk, ice, berg, dist=3000.0, n=100):
    return {"travel_time_h": time_h, "fuel_liters": fuel,
            "mean_hazard": risk, "max_hazard": risk + 0.05,
            "ice_exposure_frac": ice, "mean_iceberg_hazard": berg,
            "distance_km": dist, "n_cells": n}


def _plan():
    """Engineered trade-off: fastest is quick but risky, safest the reverse,
    balanced in between on every metric."""
    return {
        "vessel_id": "test_rv",
        "depart_date": "2020-01-15",
        "routes": {
            "fastest": _route(100.0, 1000.0, 0.30, 0.20, 0.10),
            "safest": _route(140.0, 1300.0, 0.05, 0.02, 0.01),
            "balanced": _route(115.0, 1080.0, 0.12, 0.08, 0.04),
        },
        "confidence": {"overall_confidence": 0.72, "status_label": "MEDIUM"},
        "baseline_shortest_path": {"found": True, **_route(150.0, 1400.0, 0.35, 0.30, 0.12)},
    }


# -------------------------------- comparison (FR-25) ---------------------
def test_comparison_builder_includes_baseline_and_shared_confidence():
    comp = build_comparison(_plan())
    assert comp["routes_available"]
    assert comp["baseline_included"]
    assert [r["route"] for r in comp["rows"]] == [
        "fastest", "safest", "balanced", "baseline_shortest_path"]
    assert all(r["confidence_shared_across_routes"] for r in comp["rows"])
    assert all(r["confidence"] == pytest.approx(0.72) for r in comp["rows"])


def test_comparison_markdown_renders_master_table():
    md = comparison_markdown(build_comparison(_plan()))
    assert "| Route |" in md and "fastest" in md and "safest" in md


def test_no_route_comparison_passthrough():
    comp = build_comparison({"vessel_id": "ow", "routes": {},
                             "reason": "ice-locked", "details": {"a": 1}})
    assert not comp["routes_available"]
    assert comp["reason"] == "ice-locked"
    assert "no routes" in comparison_markdown(comp)


# -------------------------------- recommendation (FR-26) -----------------
def test_profiles_pick_expected_winners():
    comp = build_comparison(_plan())
    assert recommend(comp, "balanced")["recommended"] == "balanced"
    assert recommend(comp, "safety_first")["recommended"] == "safest"
    assert recommend(comp, "time_first")["recommended"] == "fastest"


def test_sensitivity_profile_switch_moves_recommendation():
    comp = build_comparison(_plan())
    winners = {recommend(comp, p)["recommended"] for p in
               ("balanced", "safety_first", "time_first")}
    assert len(winners) > 1  # priorities change the answer (master §27)


def test_scores_bounded_and_weights_sum_to_one():
    comp = build_comparison(_plan())
    rows = [r for r in comp["rows"] if r["route"] in ("fastest", "safest", "balanced")]
    for profile, w in PRIORITY_PROFILES.items():
        assert sum(w.values()) == pytest.approx(1.0)
        for s in score_routes(rows, w).values():
            assert 0.0 <= s <= 1.0


def test_deltas_match_hand_computation():
    # balanced (115 h) vs fastest (100 h): +15.0%; vs safest (140 h): -17.9%
    assert delta_pct(115.0, 100.0) == pytest.approx(15.0)
    assert delta_pct(115.0, 140.0) == pytest.approx(-17.9, abs=0.05)
    assert delta_pct(0.0, 0.0) == 0.0
    assert delta_pct(0.05, 0.0) is None  # zero baseline -> null, never inf


def test_recommendation_carries_deltas_and_reasons():
    rec = recommend(build_comparison(_plan()), "balanced")
    assert rec["recommended"] == "balanced"
    assert set(rec["deltas_vs_alternatives_pct"]) == {"fastest", "safest"}
    assert rec["deltas_vs_alternatives_pct"]["fastest"]["travel_time_h"] == pytest.approx(15.0)
    assert rec["reasons"]  # structured evidence for Phase 14
    assert any(r["better"] for r in rec["reasons"])


def test_exact_tie_breaks_to_balanced():
    plan = _plan()
    plan["routes"] = {k: _route(100.0, 1000.0, 0.10, 0.05, 0.02)
                      for k in ("fastest", "safest", "balanced")}
    rec = recommend(build_comparison(plan), "safety_first")
    assert rec["recommended"] == "balanced"
    assert rec["tied"]
    assert any("tie-break" in c for c in rec["caveats"])


def test_low_confidence_adds_caveat_not_silent_rerank():
    plan = _plan()
    plan["confidence"] = {"overall_confidence": 0.10, "status_label": "DEGRADED"}
    rec = recommend(build_comparison(plan), "balanced")
    assert rec["recommended"] == "balanced"  # ranking unchanged ...
    assert any("FR-14" in c for c in rec["caveats"])  # ... but flagged


def test_no_route_recommendation_passthrough():
    rec = recommend(build_comparison({"vessel_id": "ow", "routes": {},
                                      "reason": "ice-locked"}), "balanced")
    assert rec["recommended"] is None
    assert "ice-locked" in rec["reason"]


def test_unknown_profile_raises():
    with pytest.raises(KeyError):
        recommend(build_comparison(_plan()), "warp_speed")
