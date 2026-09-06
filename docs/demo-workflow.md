# Demo Workflow — SIH26059

**Phase:** 20 · **NFR-2:** Fully offline · **NFR-3:** < 2 min

---

## Quick Start

```bash
# One command to launch everything:
python scripts/demo/start_demo.py

# Or verify readiness without opening:
python scripts/demo/start_demo.py --check
```

This starts:
- **API server** at http://localhost:8000 (FastAPI + interactive docs at /docs)
- **UI** at http://localhost:5173 (React + MapLibre, zero network)

Both servers run fully offline against the bundled feature store (NFR-2).

---

## Operator Workflow (NFR-3, < 2 min)

| Step | Action | What you see |
|------|--------|-------------|
| 1 | Open http://localhost:5173 | Map loads with real OSI SAF sea-ice for Jan 15, 2020. Three route lines visible. |
| 2 | **Vessel** → select "Polar Class PC7" | Routes computed: fastest 291.1h, safest 291.7h, balanced 291.8h |
| 3 | **View** → "Plan: 3 routes" (default) | Trade-off table shows time, fuel, risk, ice exposure for all three options |
| 4 | **Priorities** → try "safety first" | Winner star moves to the optimal route under the new priority weights |
| 5 | Click "Why this advice" tab | Headline recommendation + strengths + prices + vessel-fit statement |
| 6 | Click "Data status" tab | Departure date, confidence (10% DEGRADED), source list, honesty footer |
| 7 | Toggle "ice" checkbox | Sea-ice overlay on/off — see the ice-edge retreat |
| 8 | Toggle "hazard field" checkbox | Risk heatmap over the corridor (PC7 only) |
| 9 | **View** → "Update B: iceberg alarm" | Re-route notice: "1 new iceberg fix appeared; danger jump 0.999" |
| 10 | Check the map | Grey dashes = previous course, green = new advice |

**Timing:** The full workflow above takes ~30 seconds of operator actions.
The underlying computation (loading + planning + rerouting) completes in **2.95 seconds** (verified by `scripts/demo/verify_timing.py`).

---

## What Each Number Means (NFR-4 Provenance)

Every number in the UI traces to a recorded computation or the real feature store:

| Number | Source | Method |
|--------|--------|--------|
| Travel time (h) | Time-aware Dijkstra (Phase 12) | Vessel speed + current projection per edge |
| Fuel (L) | Vessel fuel model (Phase 11) | Base rate × ice load × weather penalty |
| Risk [0-1] | Unified hazard field (Phase 10) | 35% sea-ice + 35% iceberg + 20% weather + 10% ocean |
| Ice on path (%) | OSI SAF SIC CDR (CC-BY-4.0) | Fraction of route cells with SIC > 15% |
| Confidence | Phase 9 formula | Horizon degradation + staleness + missing inputs |
| Explanation | Phase 14 templates | Deterministic, no LLM, significance-guarded |
| Re-route trigger | Phase 15 change detection | Configurable thresholds (FR-32) |

**Modeled vs. observed:** all environmental data is from real satellite products (OSI SAF, ERA5). Route computations are modeled. The system is a decision-support prototype, not a certified navigation system.

---

## Verification Scripts

| Script | Purpose | Expected output |
|--------|---------|-----------------|
| `python scripts/demo/start_demo.py --check` | Verify API + UI start correctly | "Check mode: all services ready" |
| `python scripts/demo/verify_timing.py` | NFR-3 timing verification | TOTAL < 120s (actual: ~3s) |
| `python scripts/demo/verify_timing.py --json` | Machine-readable timing report | JSON with per-step timings |
| `python scripts/api/run_api.py --check` | API endpoint smoke test | All endpoints return 200 |

---

## Architecture (for judges)

```
┌─────────────────────────────────────────────────────────┐
│  React + MapLibre UI (offline, no network)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │ Map View │ │ Routes   │ │ Explain  │                │
│  │ (ice +   │ │ (table + │ │ (why +   │                │
│  │  hazard  │ │  winner) │ │  status) │                │
│  │  + bergs)│ │          │ │          │                │
│  └──────────┘ └──────────┘ └──────────┘                │
└─────────────────────┬───────────────────────────────────┘
                      │ REST/JSON (FR-33)
┌─────────────────────▼───────────────────────────────────┐
│  FastAPI Backend (Phase 18)                              │
│  POST /plan  POST /reroute  GET /validation              │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  Backend Modules (Phases 4-16)                           │
│  Forecast → Hazard → Uncertainty → Routing → Tradeoff    │
│  → Explanation → Rerouting                               │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  Feature Store (real satellite data, Dec 2019-Mar 2020)  │
│  OSI SAF SIC + ERA5 + drift (106 days, 25 km grid)      │
└─────────────────────────────────────────────────────────┘
```

---

## Honest Limitations (for judges)

1. **GLORYS12 gap:** Ocean currents use wind-driven fallback (2% wind slip, -20° deflection). Confidence is DEGRADED.
2. **Corridor fixed:** Bharati→Maitri only. Free origin/destination via API, not yet in the UI.
3. **Iceberg tracks:** Demo uses labeled ASSUMED fixes. Real BYU/NIC tracks need manual download.
4. **Single season:** Trained on Dec 2019–Mar 2020. Multi-season training available but not yet deployed to the UI.
