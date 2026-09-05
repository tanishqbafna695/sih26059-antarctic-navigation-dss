# Phase 0 — Project Definition

**SIH26059** · AI-Enabled Antarctic Sea-Ice, Iceberg Trajectory, and Navigation Decision Support System
**Owner:** Ministry of Earth Sciences / NCPOR · **Status:** APPROVED BY TEAM (gate 0) · **Date:** 2026-09-04

---

## 1. Problem definition

### 1.1 The stated problem (SIH)

Develop an AI/ML-enabled decision support platform capable of forecasting Antarctic sea-ice
concentration, predicting iceberg trajectories, and identifying safe and fuel-efficient
navigation routes for research vessels using satellite, oceanographic, and meteorological datasets.

### 1.2 The real problem we solve

**Decision-making under uncertain and changing Antarctic environmental conditions.**

A vessel operator needs to know not just *what the environment will be*, but *what to do about
it*: which of several routes best fits this vessel, how the safety/time/fuel trade-offs compare,
how confident the system is, why it recommends what it does, and when the answer changes.

### 1.3 Pipeline the system realizes

```
Environmental Data → Environmental Forecast → Uncertainty → Polar Hazard Field
→ Vessel-Specific Navigability → Multiple Route Alternatives → Risk/Time/Fuel Trade-Off
→ Explainable Recommendation → Dynamic Re-Routing
```

---

## 2. Project thesis

> **An uncertainty-aware, vessel-specific navigation decision layer that converts changing
> Antarctic environmental forecasts into explainable route alternatives and continuously
> updates the recommendation.**

Positioning language: "our system focuses on…", "our contribution is…", "our architecture
integrates…". We do **not** claim "nobody has done this before."

---

## 3. Scope

### 3.1 MUST HAVE (MVP — non-negotiable)

1. Environmental dataset (sea ice + wind/ocean forcing, real public data, curated scenario)
2. Sea-ice representation and forecast (ML vs. persistence baseline)
3. Iceberg trajectory prediction (ML vs. constant-velocity baseline, probabilistic output)
4. Vessel-specific polar hazard field
5. Vessel digital model (ice class, draft, speeds, fuel, operational limits)
6. Multi-objective route optimization (configurable weights; hard vs. soft constraints)
7. Three route alternatives: Fastest, Safest, Balanced
8. Risk / time / fuel comparison table
9. Explainable recommendation ("why this route")
10. Dynamic re-routing on environment change (the demo moment)
11. Baseline benchmarking for every predictive component
12. Basic uncertainty representation on all predictions

### 3.2 SHOULD HAVE

- Probabilistic uncertainty calibration, historical backtesting, sensitivity analysis,
  missing-data handling with honest confidence degradation, live-ish data refresh.

### 3.3 COULD HAVE (only after MUST/SHOULD are proven)

- Digital twin, fleet optimization, mission planning, LLM assistant, Arctic extension,
  production deployment. **Do not build these at the expense of the core loop.**

### 3.4 NOT NOW

- Certified operational navigation, regulatory compliance, real-time operational feeds,
  cybersecurity-hardened deployment.

### 3.5 Scope test

Every proposed feature is classified MUST / SHOULD / COULD / NOT NOW and asked:
*does this improve the core decision loop (observe→predict→hazard→vessel→route→explain→re-route)?*
If not, it is deferred. **The biggest project risk is scope creep.**

---

## 4. Objectives

Demonstrate the system end-to-end (final success criteria):

| Capability   | Evidence required                                                            |
| ------------ | ---------------------------------------------------------------------------- |
| Prediction   | Sea-ice forecast with numbers vs. persistence baseline                        |
| Iceberg      | Trajectory forecast with position-error numbers vs. constant-velocity baseline |
| Uncertainty  | Confidence communicated on every forecast                                     |
| Hazard       | Combined sea-ice + iceberg + weather + vessel hazard field                     |
| Vessel       | Same environment + different vessel ⇒ different optimal route                  |
| Routing      | Fastest / Safest / Balanced alternatives generated                             |
| Trade-off    | Time / fuel / risk comparison exposed                                          |
| Explanation  | Why a route is recommended (hazards, trade-offs, confidence)                   |
| Re-routing   | Environment change ⇒ recommendation change, explained                          |
| Validation   | Baselines, backtests, sensitivity, missing-data, extreme scenarios             |
| SIH defense  | Problem, existing work, contribution, validation, why the decision layer matters |

---

## 5. Novelty positioning (defensible differentiation)

Existing systems (IcySea, BAS PolarRoute/Logist, Polar View, DESIDE, academic systems, NCPOR
work) already provide observations, forecasts, and routing. **Our contribution is the unified
decision layer**: probabilistic environmental predictions → vessel-specific hazard field →
explicit multi-route trade-offs → explainable recommendation → dynamic re-routing, with
uncertainty exposed at every step. All competitor claims are verified with sources in
Phase 1; all claims about our work are tracked in `docs/innovation-claims.md`.

---

## 6. Success metrics (targets to be confirmed experimentally — never fabricated)

| Component          | Baseline                     | Target for our system                    |
| ------------------ | ---------------------------- | ---------------------------------------- |
| Sea-ice forecast   | Persistence                  | Lower MAE/RMSE than baseline at 1–5 days |
| Iceberg trajectory | Constant-velocity extrapolation | Lower position error at 24–72 h           |
| Routing            | Shortest path                | Lower modeled hazard exposure for similar time |
| Recommendation     | No explanation               | Explicit trade-off + reason + confidence  |

All headline numbers used in judging must come from real experimental runs recorded in the
phase gate log. Targets above are goals, not results.

---

## 7. Constraints & assumptions

### 7.1 Prototype (what we build)

Public datasets, historical/curated scenarios, modeled vessel parameters, simplified but
documented fuel model, research-grade ML, offline forecasting, simulated real-time updates.

### 7.2 Production (what we explicitly do NOT claim)

Operational feeds, certified navigation integration, regulatory compliance, engineering-grade
vessel data, rigorous safety certification, cybersecurity/redundancy. The prototype is a
**research decision-support prototype**, not a certified system. Safety claims are modeled
risk criteria only.

### 7.3 Vessel safety model

Routing distinguishes **hard constraints** (route rejected: capability exceeded) from **soft
constraints** (cost increases: moderate ice, weather). High uncertainty must influence route
choice (never blindly prefer lowest expected risk with very high uncertainty).

### 7.4 Zero-cost constraint (hard, team-approved)

The project must be built and demonstrated **entirely without spending money**:

- **Datasets:** free, openly licensed public products only (e.g., OSI-SAF, NSIDC, ERA5, Copernicus); no paid subscriptions or data purchases.
- **Software:** open-source stack only (Python, FastAPI, React, MapLibre, …); no paid APIs, SDKs, model services, or SaaS tiers.
- **Compute:** local machines and free tiers only; models kept small enough to train and demo offline.
- **Hosting/deployment:** free tiers or a fully local demo; no paid cloud spend. GitHub free tier is the public home for this repo.
- **Compliance check:** every phase gate verifies zero-cost compliance; any paid option is rejected and replaced with a free equivalent.

---

## 8. Risks

| # | Risk | Mitigation |
| - | ---- | ---------- |
| 1 | Dataset access/size/licensing (OSI-SAF/NSIDC, ERA5-scale volumes) | Evaluate before committing (Phase 3); bundle one curated scenario; document licenses |
| 2 | Scarce iceberg ground truth south of ~60°S | Physics-informed synthetic tracks labeled as synthetic; validate against available real tracks |
| 3 | Overclaiming accuracy/novelty | Innovation ledger; baseline comparisons; honest limitation statements |
| 4 | Demo fragility (live map, big data) | Pre-bundled scenario + offline deterministic demo mode |
| 5 | Scope creep (LLM, digital twin, Arctic) | MUST/SHOULD/COULD gate on every feature proposal |
| 6 | Weak judge defense ("why not IcySea/PolarRoute") | Phase 1 verified comparison matrix; `docs/competitive-defense.md` |
| 7 | Fabricated or unverifiable metrics | No-fake-completion rule; every metric traced to a run in the gate log |
| 8 | Team skill spread (ML/geo/frontend) | Modular phases; baseline-first model progression; early spike in Phase 3/4 |
| 9 | Cost creep (paid datasets/APIs/hosting/compute) | Zero-cost constraint (§7.4) checked at every gate; free/open substitutes only |

---

## 9. Architecture summary

```
DATA SOURCES (satellite, sea ice, icebergs, weather, ocean, historical)
   → DATA PROCESSING (validation, cleaning, alignment, features, QC)
   → ENVIRONMENT STATE
   → {Sea-Ice ML forecast | Iceberg trajectory ML | Weather/Ocean layer}
   → UNCERTAINTY ENGINE
   → POLAR HAZARD FIELD H(x,t,v)
   → VESSEL DIGITAL MODEL
   → ROUTE OPTIMIZATION (multi-objective)
   → {FASTEST | SAFEST | BALANCED}
   → TRADE-OFF ENGINE → EXPLANATION ENGINE → HUMAN NAVIGATOR
   → MONITOR: environment changes → RE-ROUTING loop
```

Planned stack (confirmed): Python + FastAPI backend; ML via scikit-learn/XGBoost → PyTorch
only if baselines prove insufficient; xarray/GeoPandas/Rasterio geospatial; NetworkX +
multi-objective optimization for routing; React + TypeScript + MapLibre frontend.

---

## 10. Operating rules

1. **Phase gates**: strict phases 0–21; a phase never starts until the previous gate passes
   and the team approves (gate reports logged in `docs/phase-gate-log.md`).
2. **No fake completion**: "done" means implemented, tested, validated, documented.
3. **Baselines first**: persistence → classical ML → deep learning → probabilistic, moving up
   only when justified.
4. **Research before claims**: authoritative sources; facts vs. assumptions distinguished;
   sources recorded.
5. **Data provenance & quality**: every dataset documented (source, res, units, CRS, missing
   rate, license); predictions traceable dataset → preprocessing → model → output.
6. **Failure honesty**: failures reported as ERROR/CAUSE/IMPACT/FIX/VERIFICATION; missing data
   degrades confidence and says so; no-route conditions state *no acceptable route found* with
   the blocking reason.

## 11. Phase map (0–21)

0 Definition · 1 Existing solutions & gap · 2 Requirements · 3 Data strategy · 4 Data pipeline ·
5 Baselines · 6 Sea-ice forecasting · 7 Iceberg trajectory · 8 Weather/ocean layer ·
9 Uncertainty engine · 10 Hazard field · 11 Vessel model · 12 Route optimization ·
13 Trade-off engine · 14 Explanation engine · 15 Dynamic re-routing · 16 Backtesting ·
17 User interface · 18 End-to-end integration · 19 Validation & credibility · 20 Demo mode ·
21 SIH winning strategy & judge defense.

## 12. Decisions & assumptions (Phase 0)

| Decision | Choice |
| -------- | ------ |
| Working rhythm | One phase per explicit team approval (gate discipline) |
| Timeline | Weeks of preparation before SIH — build properly, compress only if needed |
| Stack | FastAPI (Python) + React/TypeScript + MapLibre |
| Data strategy | Real public data + one curated scenario; physics-informed synthetic iceberg tracks where labeled data is absent (always labeled as synthetic) |
| Repo layout | README/docs/data/backend/frontend/models/tests/configs/scripts (no top-level `src/`; backend+frontend split covers it) |
| Git | Meaningful commits per phase milestone |
| Zero-cost build | Hard constraint: free/open datasets, open-source stack, free-tier or fully local demo (§7.4) |
