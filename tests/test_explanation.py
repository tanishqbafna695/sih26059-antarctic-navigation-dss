"""Phase 14 tests: recommendation + change explanation (FR-27, FR-28)."""
from __future__ import annotations

from backend.explanation import explain_change, explain_recommendation


def _row(route, time_h, fuel, risk, ice, berg):
    return {"route": route, "travel_time_h": time_h, "fuel_liters": fuel,
            "mean_hazard": risk, "max_hazard": risk + 0.05,
            "ice_exposure_frac": ice, "mean_iceberg_hazard": berg,
            "distance_km": 3000.0, "n_cells": 100,
            "confidence": 0.72, "confidence_label": "MEDIUM"}


def _rec_balanced():
    return {
        "recommended": "balanced", "profile": "balanced",
        "deltas_vs_alternatives_pct": {
            "fastest": {"travel_time_h": 15.0, "fuel_liters": 8.0,
                        "mean_hazard": -60.0, "ice_exposure_frac": -60.0,
                        "mean_iceberg_hazard": -60.0},
            "safest": {"travel_time_h": -17.9, "fuel_liters": -16.9,
                       "mean_hazard": 140.0, "ice_exposure_frac": 300.0,
                       "mean_iceberg_hazard": 300.0},
        },
        "caveats": ["demo caveat"],
    }


VESSEL = {"name": "PC7 test", "ice_class": "PC7", "max_sic_limit": 0.6}
ROWS = [_row("fastest", 100.0, 1000.0, 0.30, 0.20, 0.10),
        _row("safest", 140.0, 1300.0, 0.05, 0.02, 0.01),
        _row("balanced", 115.0, 1080.0, 0.12, 0.08, 0.04)]


def test_headline_names_winner_with_numbers():
    exp = explain_recommendation(ROWS, _rec_balanced(), VESSEL)
    assert exp["explained"]
    assert "balanced" in exp["headline"]
    assert "115.0 h" in exp["headline"] and "0.120" in exp["headline"]


def test_strengths_and_prices_cover_both_sides():
    exp = explain_recommendation(ROWS, _rec_balanced(), VESSEL)
    assert any("less predicted risk" in s and "fastest" in s
               for s in exp["strengths"])
    assert any("more predicted risk" in p and "safest" in p
               for p in exp["prices"])


def test_noise_delta_suppressed_by_absolute_guard():
    rows = [_row("fastest", 100.0, 1000.0, 0.10, 0.05, 0.0002),
            _row("balanced", 101.0, 1005.0, 0.10, 0.05, 0.0001)]
    rec = {"recommended": "balanced", "profile": "balanced",
           "deltas_vs_alternatives_pct": {
               "fastest": {"travel_time_h": 1.0, "fuel_liters": 0.5,
                           "mean_hazard": 0.0, "ice_exposure_frac": 0.0,
                           "mean_iceberg_hazard": -50.0}},
           "caveats": []}
    exp = explain_recommendation(rows, rec, VESSEL)
    assert not any("iceberg" in s for s in exp["strengths"])  # 0.0001 abs: noise


def test_negligible_cost_note_when_winner_costs_nothing():
    rows = [_row("fastest", 120.0, 1200.0, 0.20, 0.10, 0.05),
            _row("balanced", 100.0, 1000.0, 0.05, 0.02, 0.01)]
    rec = {"recommended": "balanced", "profile": "balanced",
           "deltas_vs_alternatives_pct": {
               "fastest": {"travel_time_h": -16.7, "fuel_liters": -16.7,
                           "mean_hazard": -75.0, "ice_exposure_frac": -80.0,
                           "mean_iceberg_hazard": -80.0}},
           "caveats": []}
    exp = explain_recommendation(rows, rec, VESSEL)
    assert any("negligible" in p for p in exp["prices"])


def test_vessel_statement_and_caveats():
    exp = explain_recommendation(ROWS, _rec_balanced(), VESSEL)
    assert "PC7" in exp["vessel_statement"] and "60%" in exp["vessel_statement"]
    assert "0.170" in exp["vessel_statement"]  # balanced max hazard 0.12+0.05
    assert exp["caveats"] == ["demo caveat"]
    assert "guarantee" in exp["text"]


def test_no_route_yields_honest_non_explanation():
    exp = explain_recommendation(
        [], {"recommended": None, "reason": "ice-locked"}, VESSEL)
    assert not exp["explained"]
    assert "ice-locked" in exp["text"]


def test_change_detects_switch_with_trigger_and_deltas():
    ch = explain_change(
        {"recommended": "fastest", "travel_time_h": 100.0,
         "fuel_liters": 1000.0, "mean_hazard": 0.30},
        {"recommended": "safest", "travel_time_h": 140.0,
         "fuel_liters": 1300.0, "mean_hazard": 0.05},
        trigger="new iceberg fix 40 km ahead")
    assert ch["switched"] and ch["old_winner"] == "fastest"
    assert "new iceberg fix" in ch["headline"]
    assert ch["deltas_pct"]["travel_time_h"] == 40.0
    assert ch["deltas_pct"]["mean_hazard"] < 0


def test_change_hold_case_and_missing_side():
    same = {"recommended": "safest", "travel_time_h": 140.0,
            "fuel_liters": 1300.0, "mean_hazard": 0.05}
    ch = explain_change(dict(same), dict(same), trigger="wind update")
    assert not ch["switched"] and "holds" in ch["headline"]
    bad = explain_change({"recommended": None}, same, trigger="x")
    assert not bad["explained"]


def test_change_hold_despite_remaining_course_qualifier():
    old = {"recommended": "safest (remaining course)", "travel_time_h": 172.6,
           "fuel_liters": 99913.0, "mean_hazard": 0.028}
    new = {"recommended": "safest", "travel_time_h": 172.5,
           "fuel_liters": 100096.0, "mean_hazard": 0.027}
    ch = explain_change(old, new, trigger="new observations")
    assert not ch["switched"] and "holds" in ch["headline"]


def test_explanation_is_deterministic():
    a = explain_recommendation(ROWS, _rec_balanced(), VESSEL)["text"]
    b = explain_recommendation(ROWS, _rec_balanced(), VESSEL)["text"]
    assert a == b
