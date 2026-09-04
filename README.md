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

## Honesty rules (non-negotiable)

- This is a research decision-support **prototype**, not a certified maritime navigation system.
- We do not claim to have invented polar route optimization; we position a specific decision architecture.
- Every novelty claim is tracked in `docs/innovation-claims.md` with a status: VERIFIED / INFERRED / PROPOSED / EXPERIMENTALLY VALIDATED / NOT YET VALIDATED.
- No fabricated metrics, no fake completions, no assumed competitor capabilities. Every claim carries a source.
- Safety is a *modeled risk criterion* — never a guarantee of real-world safe navigation.

## Repository layout

```
README.md              Project overview (this file)
docs/                  Definition, gate log, research, judge defense (see index below)
data/                  Datasets + curated scenario bundles (raw/processed kept separate)
backend/               Python: FastAPI service, ML/forecast pipeline, geospatial processing
frontend/              React + TypeScript + MapLibre map client
models/                Trained model artifacts + training metadata
tests/                 Unit / integration / validation tests
configs/               Environment, scenario, and model configuration
scripts/               Reproducibility scripts (data fetch, training, demo)
```

## Docs index

| File                                   | Purpose                                            | Phase |
| -------------------------------------- | -------------------------------------------------- | ----- |
| `docs/project-definition.md`           | Phase 0 deliverable: problem, scope, objectives    | 0     |
| `docs/phase-gate-log.md`               | Running record of every phase gate report          | all   |
| `docs/existing-solutions-gap.md`       | Verified competitor analysis and gap               | 1     |
| `docs/innovation-claims.md`            | Claim ledger with evidence and status              | 1+    |
| `docs/data-strategy.md`                | Dataset selection, licenses, preprocessing         | 3     |
| `docs/judge-questions.md`              | Evidence-backed judge defense                      | 21    |
| `docs/sih-winning-strategy.md`         | Winning strategy                                   | 21    |
| `docs/competitive-defense.md`          | "Why not IcySea / PolarRoute" defense              | 21    |

## Working method

The project runs through strict phases (0–21). Each phase ends with a gate report in
`docs/phase-gate-log.md`; **no phase begins until the previous gate passes and the team approves.**
See `docs/project-definition.md` for the phase list and operating rules.

## How to run

Placeholder — populated once the backend/frontend scaffolds land (Phase 12+ integration, Phase 20 demo mode).

---
*Team-internal working title. Final product naming is a Phase 20 decision.*
