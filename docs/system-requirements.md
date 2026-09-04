# System Requirements — SIH26059

**Phase:** 2
**Status:** DRAFT FOR APPROVAL (gate 2)
**Date:** 2026-09-04
**Traceability:** requirement IDs (FR-x / NFR-x / SC-x) are referenced by later phases and by the acceptance test matrix (Phase 16/19). Priorities follow the Phase 0 scope (MUST / SHOULD / COULD / NOT NOW).

---

## 1. Purpose

Define what the system must do, for whom, under what constraints, and how we will know it works — before any implementation. This document is the contract between the problem (Phase 0) and the build (Phases 3–18).

---

## 2. Users & stakeholders

| ID | User | Role | Primary needs |
| --- | --- | --- | --- |
| U1 | **Navigator / Officer of the Watch** (research vessel) | Primary operator during voyage | Understand current & forecast ice/iceberg conditions; see route options with risks; act on an explained recommendation; be alerted when conditions change and the recommendation moves |
| U2 | **Voyage / logistics planner** (ashore) | Chooses route and timing before departure | Compare scenarios (vessel, dates); weigh time/fuel/risk; export/record decisions |
| U3 | **NCPOR / MoES mission staff** | Problem owner; Antarctic logistics | Trustworthy decision support for Indian Antarctic operations (e.g., Bharati–Maitri resupply corridor) |
| U4 | **SIH judges / demo audience** | Evaluators | Understand the problem; see the decision loop work live; hear honest claims backed by numbers |
| U5 | **Developer / maintainer (team)** | Builds and validates | Clean module boundaries; reproducible runs; documented data provenance; testable units |

**Human-in-the-loop rule (all users):** the system recommends and explains; it never claims to replace the navigator or to guarantee safety. All UIs and outputs carry decision-support framing.

---

## 3. Inputs (data the system consumes)

All inputs carry provenance metadata (source, timestamp, spatial/temporal resolution, units, CRS, license, missing-data rate). Details and sources are decided in Phase 3; these are the requirement-level contracts.

| ID | Input | Role | Minimum requirement (prototype) |
| --- | --- | --- | --- |
| IN-1 | Sea-ice concentration (SIC) fields, observed | Nowcast state + training | Gridded Antarctic coverage, daily or better, ~6–25 km; ≥ 1 season (target: multi-year) |
| IN-2 | Sea-ice drift / motion | Iceberg forcing + baseline | Gridded drift vectors where available; else derived from SIC time series |
| IN-3 | Iceberg observations / tracks | Trajectory model + validation | Catalog of iceberg positions/tracks with times (real where available; physics-informed synthetic tracks **labeled synthetic** where not) |
| IN-4 | Atmospheric forcing (wind u/v, temp, pressure) | Iceberg drift, hazard, fuel | Gridded reanalysis-class fields (e.g., ERA5-scale), daily or better |
| IN-5 | Ocean forcing (surface currents, SST) | Drift + hazard | Gridded currents/SST (Copernicus-class) where available; documented fallback (climatology / zeros with reduced confidence) |
| IN-6 | Vessel parameters | Vessel model | Modeled profile: ice class, draft, max/cruise speed, fuel curve, ice/weather limits (flagged as modeled; editable) |
| IN-7 | Voyage request | Routing | Origin, destination, departure time, priority weights (α safety, β time, γ fuel), optional waypoints |
| IN-8 | Land / coastline / protected-area masks | Routing constraints | Hard obstacles for the route graph |
| IN-9 | Scenario catalog (curated) | Demo + tests | Pre-bundled environmental snapshots incl. one Bharati–Maitri scenario and failure scenarios (SC-7) |

---

## 4. Outputs (products the system exposes)

| ID | Output | Description |
| --- | --- | --- |
| OUT-1 | Environmental forecast products | Sea-ice concentration forecast (1–5 days) with uncertainty; iceberg trajectory probability per tracked iceberg (24–72 h); weather/ocean forecast layer |
| OUT-2 | Hazard field | Unified vessel-specific hazard H(x, t, v) over the route domain, decomposed by contributor (ice / iceberg / weather / ocean) |
| OUT-3 | Route set | Fastest, Safest, Balanced alternatives as geospatial polylines with time-stamped legs |
| OUT-4 | Trade-off table | Per-route: est. time, fuel, risk, ice exposure, iceberg exposure, uncertainty/confidence |
| OUT-5 | Recommendation + explanation | One recommended route; human-readable reasons (hazard deltas %, avoided features, vessel-capability statement, confidence, caveats) |
| OUT-6 | Re-route notices | When environment changes: old vs. new route, trigger explanation, delta metrics |
| OUT-7 | Data-status panel | Per-input freshness, missing-data flags, confidence impact ("iceberg obs unavailable 6 h → trajectory confidence high→medium") |
| OUT-8 | No-route statement | If no acceptable route: blocking hazard(s), affected region, vessel limitation, next-reassessment time — **never a fake route** |
| OUT-9 | Provenance report | For any displayed quantity: dataset → preprocessing → model → output chain |
| OUT-10 | Validation report | Baselines vs. model metrics from recorded runs (Phase 16+; also used by judges) |

---

## 5. Functional requirements

Priorities: **M** = MUST (MVP), **S** = SHOULD, **C** = COULD. All MUSTs gate the final demo.

### 5.1 Data ingestion & quality (Phase 4)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-1 | M | Ingest IN-1…IN-5 from documented sources or curated scenario files with format validation |
| FR-2 | M | Normalize CRS, grids, units, timestamps to one internal convention; record per-field provenance |
| FR-3 | M | Detect missing/stale data per input; mark affected outputs; degrade confidence explicitly (never silent) |
| FR-4 | S | Interpolate only where justified; log every interpolation and its assumptions |

### 5.2 Sea-ice forecast (Phase 6)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-5 | M | Produce SIC forecast at 1–5 day horizons from a trained ML model |
| FR-6 | M | Produce persistence baseline for identical horizons; report MAE/RMSE both |
| FR-7 | M | Attach uncertainty (per-grid-cell or per-region) to every forecast |

### 5.3 Iceberg trajectory (Phase 7)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-8 | M | Predict probability distribution of future positions for each tracked iceberg at 24/48/72 h |
| FR-9 | M | Produce constant-velocity baseline; report position error (km) both |
| FR-10 | M | Treat synthetic tracks transparently (labeled) when real ground truth is absent |
| FR-11 | S | Update trajectory as new observations arrive; widen uncertainty with staleness |

### 5.4 Uncertainty engine (Phase 9)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-12 | M | Every displayed forecast/prediction shows observed vs. estimated vs. forecast status + confidence |
| FR-13 | M | Confidence degrades with missing inputs, forecast horizon, and model uncertainty |
| FR-14 | S | High uncertainty must be able to change route ranking (uncertainty-aware decision rule) |

### 5.5 Hazard field (Phase 10)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-15 | M | Combine SIC, iceberg probability, weather, ocean into H(x, t, v) with documented weights/formula |
| FR-16 | M | Expose per-contributor decomposition for explanation |
| FR-17 | M | Enforce hard constraints (reject) vs. soft constraints (cost) distinctly |

### 5.6 Vessel model (Phase 11)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-18 | M | Model vessel: ice class, draft, max/cruise speed, fuel curve, ice/weather operational limits |
| FR-19 | M | Mark modeled parameters as modeled; allow editing |
| FR-20 | M | Same environment + different vessel ⇒ potentially different optimal route (demonstrable) |

### 5.7 Routing (Phase 12)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-21 | M | Shortest-path baseline route (graph over cost field, obstacles from IN-8) |
| FR-22 | M | Fastest, Safest, Balanced routes via multi-objective optimization with configurable weights |
| FR-23 | M | Route costs use forecast hazard at times the vessel actually transits each cell (time-aware) |
| FR-24 | M | No acceptable route ⇒ OUT-8 statement with reasons, never a fake route |

### 5.8 Trade-off engine (Phase 13)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-25 | M | Compare routes on time, fuel, risk, ice exposure, iceberg exposure, confidence |
| FR-26 | M | Recommend one route by active weights; show why via % deltas vs. alternatives |

### 5.9 Explanation engine (Phase 14)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-27 | M | Explain recommendation: hazard deltas, avoided regions, vessel-capability statement, confidence, caveats |
| FR-28 | S | Explain any route change (old → new) with the triggering hazard change |
| FR-29 | C | Natural-language summary (template-based; no LLM dependency in MVP) |

### 5.10 Dynamic re-routing (Phase 15)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-30 | M | Accept environment update (new SIC, new iceberg fix, weather change) mid-voyage and recompute the full chain |
| FR-31 | M | Emit OUT-6 re-route notice: old vs. new route, trigger, delta metrics |
| FR-32 | S | Trigger thresholds configurable (how big a change forces a re-route) |

### 5.11 API & application (Phase 18)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-33 | M | REST/JSON API (FastAPI) exposing scenario → forecast → hazard → routes → recommendation → re-route |
| FR-34 | M | Deterministic offline demo mode replaying a bundled scenario |
| FR-35 | S | Server-sent events / polling endpoint for environment updates during demo |
| FR-36 | S | Validation endpoints: run baseline-vs-model comparisons and return metrics |

### 5.12 Frontend (Phase 17)
| ID | Pri | Requirement |
| --- | --- | --- |
| FR-37 | M | Map (MapLibre): ice fields, iceberg tracks + probability ellipses, hazard layer, routes, vessel position |
| FR-38 | M | Panels: trade-off table (OUT-4), recommendation + explanation (OUT-5), data status (OUT-7) |
| FR-39 | M | Controls: select vessel, origin/destination, weights; trigger scenario update (demo re-route) |
| FR-40 | S | Side-by-side old vs. new route visualization on re-route |

---

## 6. Non-functional requirements

| ID | Category | Requirement |
| --- | --- | --- |
| NFR-1 | Performance | Scenario-scale route recompute (grid ≲ 10⁴–10⁵ cells, ≤ 3 objectives) completes in seconds; API typical < 2 s for hazard+routes on a bundled scenario; deterministic given same inputs |
| NFR-2 | Availability / offline | Full demo runs offline from the curated scenario bundle (no network dependency at judging time) |
| NFR-3 | Usability | Core demo story executable by the team in < 2 min: select vessel → pick route pair → generate → compare → explain → change environment → re-route |
| NFR-4 | Honesty & explainability | Every number shown has a tooltip/provenance link (OUT-9); modeled/synthetic/forecast values visually distinguished from observations |
| NFR-5 | Reproducibility | Pinned dependency set + config files; recorded runs replayable (same inputs ⇒ same outputs & metrics) |
| NFR-6 | Maintainability | Module boundaries match the architecture (data / forecast / uncertainty / hazard / vessel / routing / trade-off / explanation / rerouting); each unit testable |
| NFR-7 | Data footprint | Curated scenario bundle small enough for the demo machine and the repo (documented; data/ kept lean, heavy data downloaded by script, not committed) |
| NFR-8 | Security & privacy | Prototype: no credentials in repo; public repo hygiene enforced (secrets scan before commits); no personal data |
| NFR-9 | Portability | Python 3.11+ backend and Node/TS frontend run on team machines (Windows/macOS/Linux) via documented setup |
| NFR-10 | Compliance honesty | UI/docs never claim operational certification, guaranteed safety, or production readiness |

---

## 7. Scenarios

### SC-1 Primary demo (Bharati → Maitri corridor) — MUST
A modeled polar research vessel (U1/U4) voyages from Bharati (69°24′ S, 76°11′ E) toward Maitri (70°45′ S, 11°43′ E) (or a mission leg between them via the ice edge) in a curated seasonal scenario. The system: loads environment → forecasts SIC (vs. persistence) → predicts iceberg trajectories (vs. constant-velocity) → builds hazard field → emits Fastest/Safest/Balanced → compares → recommends + explains → an update arrives → re-routes with old/new comparison. Mirrors academic benchmark Mishra et al. 2021 where data allow (Phase 16).

### SC-2 Planning review — SHOULD
Planner (U2) compares the same corridor for two vessels (different ice classes) and two departure dates; routes and recommendations differ; the planner sees why.

### SC-3 Operational nowcast — SHOULD
Navigator (U1) inspects current ice + iceberg positions along the chosen route, checks data status, sees confidence bars.

### SC-4 Missing satellite data — MUST (failure demo)
SIC or iceberg observations stop; status panel flags staleness; confidence degrades; explanation mentions the gap. No silent failure.

### SC-5 Sudden ice increase / iceberg approach — MUST (failure demo)
Scenario update raises SIC along the recommended corridor and/or moves an iceberg into it; re-route triggers; new route explained.

### SC-6 Different vessel, different answer — MUST
PC-class icebreaker vs. open-water research vessel on the same route set ⇒ different recommendation, demonstrating vessel-specificity (FR-20).

### SC-7 No viable route — MUST
Destination reachable only through conditions violating hard constraints; system returns OUT-8 with blocking hazard + next-reassessment time; no fake route.

### SC-8 Weather deterioration — SHOULD
Wind/wave hazard along the planned route increases; trade-off table updates; recommendation may shift Safest → Balanced/fastest depending on weights.

---

## 8. Constraints

| ID | Constraint |
| --- | --- |
| C-1 | Prototype only: public/curated data, modeled vessel params, simplified documented fuel model, offline forecasting, simulated real-time updates (Phase 0 §7.1) |
| C-2 | No operational certification claims; safety = modeled risk criterion with hard/soft constraint logic (Phase 0 §7.2–7.3) |
| C-3 | Scope gates: every feature classified MUST/SHOULD/COULD/NOT NOW before build (Phase 0 §3.5, §10) |
| C-4 | Baselines mandatory for every predictive component before claims (Phase 0 §6) |
| C-5 | Iceberg ground truth south of ~60° S is scarce ⇒ synthetic tracks labeled synthetic (Phase 0 §8, risk 2) |
| C-6 | Stack locked: FastAPI + React/TS + MapLibre; scikit-learn/XGBoost first, PyTorch only if justified (Phase 0 §9) |
| C-7 | Team skill spread ⇒ simple-first model progression and modular phases (Phase 0 §8, risk 8) |

---

## 9. Success metrics & acceptance criteria

Metrics are **targets** until recorded experimental runs exist (Phase 16/19 make them results). Every acceptance criterion below is testable.

| Area | Criterion | How verified |
| --- | --- | --- |
| Sea-ice forecast | ML SIC forecast beats persistence on MAE/RMSE at 1–5 d on the held-out scenario/validation window | FR-6 run log |
| Iceberg trajectory | Model position error ≤ constant-velocity baseline at 24/48/72 h on validation tracks | FR-9 run log |
| Routing | Recommended route has lower modeled hazard exposure than shortest path for ≤ some % time penalty; three routes differ measurably | FR-22/25 run log |
| Vessel-specificity | Two vessel profiles on same inputs yield different optimal route/recommendation | FR-20/SC-6 run |
| Uncertainty honesty | Every forecast/prediction carries confidence that degrades with missing data & horizon | FR-12/13 demo check |
| Re-routing | Environment update changes ≥ 1 route and recommendation with an explanation (SC-5) | FR-30/31 demo check |
| No-route | SC-7 returns OUT-8, never a route | FR-24 test |
| Demo readiness | SC-1 completes deterministically offline in < 2 min of operator actions | NFR-2/3 acceptance run |
| Baseline benchmarking | Phase 16 backtests + sensitivity + missing-data + extreme-condition tests recorded in gate log | Phase 19 report |
| Claim integrity | All headline numbers traceable to runs; innovation ledger classes respected | Gate-log + ledger audit |

**Acceptance test matrix:** a `tests/` suite + `scripts/` runner will encode FR acceptance (unit tests per module from Phase 4 onward; scenario tests SC-1…SC-8 in Phase 18/19).

---

## 10. Requirements → phase map

| Phase | Primary requirements |
| --- | --- |
| 3 Data strategy | IN-1…IN-9 sourcing |
| 4 Data pipeline | FR-1…FR-4 |
| 5 Baselines | FR-6, FR-9, FR-21 |
| 6 Sea-ice forecast | FR-5…FR-7 |
| 7 Iceberg trajectory | FR-8…FR-11 |
| 8 Weather/ocean | IN-4, IN-5 into hazard/fuel |
| 9 Uncertainty | FR-12…FR-14 |
| 10 Hazard field | FR-15…FR-17 |
| 11 Vessel model | FR-18…FR-20 |
| 12 Routing | FR-21…FR-24 |
| 13 Trade-off | FR-25…FR-26 |
| 14 Explanation | FR-27…FR-29 |
| 15 Re-routing | FR-30…FR-32 |
| 16 Backtesting | SC-1…SC-8 metrics |
| 17 UI | FR-37…FR-40 |
| 18 Integration | FR-33…FR-36, SC-1 |
| 19 Validation | §9 acceptance audit |
| 20 Demo mode | NFR-2/3, SC-1 |
