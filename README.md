# Antarctic Navigation Decision Support System

**Smart India Hackathon (SIH) — Problem Statement ID: SIH26059**
**Organization:** Ministry of Earth Sciences / National Centre for Polar and Ocean Research (NCPOR) · Category: Software

> AI-Enabled Antarctic Sea-Ice, Iceberg Trajectory, and Navigation Decision Support System

## What this project is

A decision-support platform (not a dashboard, not "just" a route planner) that converts Antarctic environmental data into **explainable, vessel-specific navigation decisions**. The system forecasts sea ice and iceberg motion with quantified uncertainty, builds a vessel-specific polar hazard field, generates competing route alternatives (Fastest / Safest / Balanced), quantifies the safety–time–fuel trade-off, explains its recommendation, and re-routes dynamically when conditions change. A human navigator remains in the loop.

## Central thesis

> Prediction is not the final problem. Decision-making under uncertainty is.

The product is an **uncertainty-aware, vessel-specific navigation decision layer** that converts changing Antarctic environmental forecasts into explainable route alternatives and continuously updates the recommendation.

## Core decision loop

```
OBSERVE → PREDICT → ESTIMATE UNCERTAINTY → ASSESS HAZARD → ACCOUNT FOR VESSEL
        → OPTIMIZE → COMPARE → EXPLAIN → DECIDE → MONITOR → RE-ROUTE
```

## Quick start

```bash
# 1. Clone and set up
git clone https://github.com/tanishqbafna695/sih26059-antarctic-navigation-dss.git
cd sih26059-antarctic-navigation-dss
python -m venv .venv && .venv/Scripts/activate  # Windows
pip install -r requirements.txt

# 2. Run the demo (one command)
python scripts/demo/start_demo.py

# 3. Open the UI at http://localhost:5173
```

The demo runs **fully offline** against the bundled real satellite data (Dec 2019 – Mar 2020, Bharati–Maitri corridor). No API keys or network required.

## Key results

| Metric | Value |
|---|---|
| Test suite | **145/145 green** (15 modules, including 20 acceptance tests) |
| Demo timing | **2.95 seconds** (NFR-3 limit: 120s) |
| Seasonal forecast vs persistence | RMSE **0.0487 vs 0.0501** at h=5 (real data) |
| PC1 routes vs shortest-path | **221.2h / risk 0.038** vs 240.2h / risk 0.064 |
| Acceptance scenarios | **SC-1 through SC-8: ALL PASS** |
| FR validation | **25/25 traced requirements validated** |

## Honesty rules (non-negotiable)

- This is a research decision-support **prototype**, not a certified maritime navigation system.
- We do not claim to have invented polar route optimization; we position a specific decision architecture.
- Every novelty claim is tracked in `docs/innovation-claims.md` with a status class.
- No fabricated metrics, no fake completions, no assumed competitor capabilities. Every claim carries a source.
- Safety is a *modeled risk criterion* — never a guarantee of real-world safe navigation.

## Repository layout

```
README.md                  Project overview (this file)
docs/                      Definition, gate log, research, judge defense
data/                      Datasets + curated scenario bundles
backend/                   Python: FastAPI, ML/forecast, geospatial processing
frontend/                  React + TypeScript + MapLibre map client
tests/                     Unit / integration / validation tests (145 tests)
configs/                   Environment, scenario, and model configuration
scripts/                   Reproducibility scripts (data fetch, demo, validation)
```

## Docs index

| File | Purpose | Phase |
|---|---|---|
| `docs/project-definition.md` | Problem, scope, objectives, phase map | 0 |
| `docs/phase-gate-log.md` | Running record of every phase gate report | all |
| `docs/existing-solutions-gap.md` | Verified competitor analysis and gap | 1 |
| `docs/innovation-claims.md` | Claim ledger with evidence and status | 1+ |
| `docs/system-requirements.md` | 40 FRs, 10 NFRs, 8 scenarios | 2 |
| `docs/data-strategy.md` | Dataset selection, licenses, preprocessing | 3 |
| `docs/account-setup.md` | Free-account registration + real-data download | 4 |
| `docs/validation-report.md` | SC-1–SC-8 acceptance + FR audit + claim #23 | 19 |
| `docs/demo-workflow.md` | Operator workflow, architecture, provenance | 20 |
| `docs/judge-defence.md` | Pitch, competitive defences, evidence summary | 21 |

## Zero-cost constraint

This project is built and demonstrated **entirely without spending money**: free/openly
licensed public datasets only, an open-source stack, no paid APIs or services, and a free-tier
or fully local demo. Every phase gate checks compliance (see `docs/project-definition.md` §7.4).

## Working method

The project runs through strict phases (0–21). Each phase ends with a gate report in
`docs/phase-gate-log.md`; **no phase begins until the previous gate passes and the team approves.**
See `docs/project-definition.md` for the phase list and operating rules.

## Test suite

```bash
# Run all 145 tests
python -m pytest tests -q

# Run only acceptance tests (SC-1 through SC-8)
python -m pytest tests/test_acceptance.py -v

# Verify demo timing (NFR-3)
python scripts/demo/verify_timing.py

# Verify API endpoints
python scripts/api/run_api.py --check
```

## License

This project uses free/open-source datasets and software. See `docs/data-strategy.md` for dataset licenses (CC-BY-4.0, Copernicus licence). All code is open-source.

---
*Built for SIH26059 by Team Freebuff. Decision-support prototype — not a certified navigation system.*
