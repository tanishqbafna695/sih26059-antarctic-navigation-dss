"""Tests for the Phase 18 REST API (FR-33–FR-36).

Uses FastAPI's TestClient (starlette.testclient.TestClient) which avoids
actually binding a port — the tests exercise the full backend chain
through the HTTP layer without network overhead.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.api.schemas import PlanRequest, LatLon

# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def pc7_plan_payload():
    return {
        "origin": {"lat": -69.41, "lon": 76.19},
        "destination": {"lat": -70.77, "lon": 11.73},
        "vessel_id": "polar_class_pc7",
        "depart_day_index": 45,
        "priority": "balanced",
    }


# ── GET /health ─────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    d = resp.json()
    assert d["status"] == "ok"
    assert d["feature_store"]["n_days"] == 106
    assert len(d["data_sources"]) >= 2
    assert "sea_ice_forecast" in d["model_versions"]


# ── GET /vessels ────────────────────────────────────────────────────────────

def test_vessels(client):
    resp = client.get("/api/v1/vessels")
    assert resp.status_code == 200
    vessels = resp.json()
    ids = [v["vessel_id"] for v in vessels]
    assert "open_water_rv" in ids
    assert "polar_class_pc7" in ids
    assert "polar_class_pc1" in ids
    for v in vessels:
        assert v["max_sic_limit"] >= 0
        assert v["cruise_speed_kts"] > 0


# ── GET /corridors ──────────────────────────────────────────────────────────

def test_corridors(client):
    resp = client.get("/api/v1/corridors")
    assert resp.status_code == 200
    cors = resp.json()
    assert len(cors) >= 1
    assert cors[0]["id"] == "bharati_maitri"
    assert cors[0]["origin"]["lat"] == pytest.approx(-69.41, abs=0.1)


# ── POST /plan — PC7 happy path ─────────────────────────────────────────────

def test_plan_pc7(client, pc7_plan_payload):
    resp = client.post("/api/v1/plan", json=pc7_plan_payload)
    assert resp.status_code == 200
    d = resp.json()
    assert d["vessel_id"] == "polar_class_pc7"
    assert d["depart_date"] == "2020-01-15"
    # Three routes expected
    assert set(d["routes"].keys()) == {"fastest", "safest", "balanced"}
    for name, r in d["routes"].items():
        assert r["travel_time_h"] > 200
        assert r["fuel_liters"] > 100000
        assert 0 <= r["mean_hazard"] < 1.0
        assert len(r["path_latlon"]) >= 10
    # Recommendation
    assert d["recommendation"]["recommended"] in ("fastest", "safest", "balanced")
    # Explanation
    assert d["explanation"]["explained"] is True
    assert "Take the" in d["explanation"]["headline"]
    # Confidence
    assert 0 <= d["confidence"]["overall_confidence"] <= 1.0
    assert d["confidence"]["status_label"] == "DEGRADED"  # GLORYS12 gap


# ── POST /plan — no-route (FR-24) ──────────────────────────────────────────

def test_plan_no_route(client):
    resp = client.post("/api/v1/plan", json={
        "origin": {"lat": -69.41, "lon": 76.19},
        "destination": {"lat": -70.77, "lon": 11.73},
        "vessel_id": "open_water_rv",
        "depart_day_index": 0,
        "priority": "balanced",
    })
    assert resp.status_code == 200
    d = resp.json()
    assert d["routes"] == {}
    assert d["recommendation"]["recommended"] is None
    assert d["explanation"]["explained"] is False
    assert "no acceptable route" in d["explanation"]["reason"].lower()


# ── POST /plan — PC1 different priority ─────────────────────────────────────

def test_plan_pc1_safety_first(client):
    resp = client.post("/api/v1/plan", json={
        "origin": {"lat": -69.41, "lon": 76.19},
        "destination": {"lat": -70.77, "lon": 11.73},
        "vessel_id": "polar_class_pc1",
        "depart_day_index": 45,
        "priority": "safety_first",
    })
    assert resp.status_code == 200
    d = resp.json()
    assert d["vessel_id"] == "polar_class_pc1"
    assert len(d["routes"]) == 3
    assert d["recommendation"]["recommended"] == "safest"


# ── POST /plan — unknown vessel (422) ──────────────────────────────────────

def test_plan_unknown_vessel(client):
    resp = client.post("/api/v1/plan", json={
        "origin": {"lat": -69.41, "lon": 76.19},
        "destination": {"lat": -70.77, "lon": 11.73},
        "vessel_id": "nonexistent_vessel",
        "depart_day_index": 45,
    })
    assert resp.status_code == 422


# ── POST /reroute ───────────────────────────────────────────────────────────

def test_reroute(client, pc7_plan_payload):
    resp = client.post("/api/v1/reroute", json={
        "old_plan": pc7_plan_payload,
        "old_priority": "balanced",
        "old_winner_route": "safest",
        "elapsed_hours": 120.0,
        "new_icebergs": [],
        "new_depart_day_index": 50,
    })
    assert resp.status_code == 200
    d = resp.json()
    assert d["outcome"] in ("RE-ROUTE", "ADJUSTED", "HOLDS", "COMPLETE")
    assert "changes" in d
    assert "confidence" in d


# ── GET /validation (FR-36) ─────────────────────────────────────────────────

def test_validation(client):
    resp = client.get("/api/v1/validation")
    assert resp.status_code == 200
    d = resp.json()
    assert "sea_ice" in d
    assert "iceberg" in d
    assert "routing" in d
    assert "data_window" in d


# ── POST /plan — all priorities produce a recommendation ────────────────────

@pytest.mark.parametrize("priority", ["balanced", "safety_first", "time_first", "fuel_saver"])
def test_plan_all_priorities(client, priority):
    resp = client.post("/api/v1/plan", json={
        "origin": {"lat": -69.41, "lon": 76.19},
        "destination": {"lat": -70.77, "lon": 11.73},
        "vessel_id": "polar_class_pc7",
        "depart_day_index": 45,
        "priority": priority,
    })
    assert resp.status_code == 200
    d = resp.json()
    assert d["recommendation"]["recommended"] in ("fastest", "safest", "balanced")
    assert d["recommendation"]["profile"] == priority


# ── Schema validation ───────────────────────────────────────────────────────

def test_schema_validation_rejects_bad_lat():
    with pytest.raises(Exception):
        PlanRequest(
            origin={"lat": 999, "lon": 0},
            destination={"lat": -70, "lon": 11},
        )
