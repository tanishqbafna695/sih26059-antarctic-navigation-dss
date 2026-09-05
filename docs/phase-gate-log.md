# Phase Gate Log

Running record of every phase gate report. A phase never begins until the previous gate
**PASSES** and the team explicitly approves. Failures are recorded, never hidden.

---

## PHASE 0 — PROJECT DEFINITION

```
PHASE:     0 — Project Definition
STATUS:    COMPLETE (awaiting team approval to begin Phase 1)

COMPLETED:
- Problem definition, project thesis, scope (MUST/SHOULD/COULD/NOT NOW)
- Objectives mapped to final success criteria
- Defensible novelty positioning + anti-overclaim rules
- Success metric targets (flagged as targets, not results)
- Constraints (prototype vs. production) and risk register
- Architecture summary + phase map (0–21) + operating rules
- Decisions captured from team Q&A (rhythm, timeline, stack, data strategy)

INCOMPLETE:
- None for Phase 0 scope

FILES CREATED:
- README.md
- docs/project-definition.md
- docs/phase-gate-log.md
- data/ backend/ frontend/ models/ tests/ configs/ scripts/ (empty scaffolds, .gitkeep)

FILES MODIFIED:
- None

TESTS:
- None (Phase 0 is definition-only; no implementation code written)

RESULTS:
- None (no experimental results exist yet; metric targets are goals only)

PROBLEMS:
- None

DECISIONS:
- One phase per explicit approval; weeks of prep; FastAPI + React/TS + MapLibre;
  real public data + curated scenario (+ labeled synthetic iceberg tracks)
- Top-level src/ omitted as redundant (backend/ + frontend/ cover it)

ASSUMPTIONS:
- Workspace was empty; greenfield scaffold created and git initialized
- SIH evaluation emphasizes decision usefulness, measurable results, honest claims

VALIDATION:
- Definition reviewed against SIH26059 official problem text and master brief sections 0–52

PHASE GATE: PASS
```

---
*Next: Phase 1 — Existing Solutions & Gap Analysis (requires team approval).*

---

## PHASE 1 — EXISTING SOLUTIONS & GAP ANALYSIS

```
PHASE:     1 — Existing Solutions & Gap Analysis
STATUS:    COMPLETE (awaiting team approval to begin Phase 2)

COMPLETED:
- Web research with primary sources for: IcySea (Drift+Noise/ESA InCubed + operator
  interview), BAS PolarRoute/Logist (arXiv paper + BAS + BAS-authored WWF article),
  DESIDE (DestinE + Polar View pages), Polar View Antarctic (polarview.aq + BAS),
  academic Antarctic routing (Mishra 2021 Bharati-Maitri; Gupta 2019 Web-GIS; NRC
  2023 review), and iceberg-monitoring reality (Arctic Institute 2026 review)
- docs/existing-solutions-gap.md: verified system profiles, comparison matrix
  (VERIFIED / partial / INFERRED legend), defensible gap statement, canned
  "Why not IcySea/PolarRoute/DESIDE" defences, architecture implications, sources
- docs/innovation-claims.md: 24-row ledger with VERIFIED / INFERRED / PROPOSED /
  NOT YET VALIDATED classes + claim-use discipline rules + positioning statement

INCOMPLETE:
- None for Phase 1 scope (competitor re-verification is a standing task before judging)

FILES CREATED:
- docs/existing-solutions-gap.md
- docs/innovation-claims.md

FILES MODIFIED:
- docs/phase-gate-log.md (this entry)

TESTS:
- None (research/documentation phase; no implementation code)

RESULTS:
- Gap identified: no surveyed public system demonstrates the full Antarctic decision
  layer (probabilistic inputs incl. iceberg trajectory -> vessel hazard -> multi-route
  trade-offs -> explained recommendation -> dynamic re-routing)
- Key nuance: IcySea route optimisation still in development (2024 operator interview);
  DESIDE is Arctic/Baltic-first; Polar View provides iceberg presence, not trajectory
  probability; PolarRoute is research-grade vessel-aware routing

PROBLEMS:
- BAS project page returned no readable text (worked around with BAS-authored WWF
  article + Zenodo record + arXiv paper)
- ScienceDirect blocked direct fetch (worked around with indexed record details)

DECISIONS:
- Route core = graph search over cost field (matches academic practice); differentiator
  is the decision layer, not the search algorithm
- Iceberg hazard baseline to beat = operational presence-based products (NAVAREA grids)
- Bharati-Maitri is our natural NCPOR demo scenario and academic benchmark
- Competitor "absence" claims recorded as INFERRED, never VERIFIED fact

ASSUMPTIONS:
- Public-material review bounded to sources listed in the gap doc (accessed 2026-09-04)
- Competitor products may have evolved beyond public material; re-verify before judging

VALIDATION:
- Matrix rows cross-checked against the claims in docs/innovation-claims.md (#1-18)
- Claims disciplined per master brief sections 17-19, 24, 38-39

PHASE GATE: PASS
```

---
*Next: Phase 2 — System Requirements (requires team approval).*

---

## PHASE 2 — SYSTEM REQUIREMENTS

```
PHASE:     2 — System Requirements
STATUS:    COMPLETE (awaiting team approval to begin Phase 3)

COMPLETED:
- docs/system-requirements.md: users/stakeholders (U1-U5), inputs (IN-1..IN-9),
  outputs (OUT-1..OUT-10), functional requirements (FR-1..FR-40 with MUST/SHOULD/COULD
  priorities), non-functional requirements (NFR-1..NFR-10), scenarios (SC-1..SC-8),
  constraints (C-1..C-7), success metrics + acceptance criteria, requirements->phase map
- All requirements traced to Phase 0 decisions (scope, stack, Bharati-Maitri scenario,
  honesty rules) and Phase 1 findings (baselines mandatory, iceberg presence-gap)

INCOMPLETE:
- None for Phase 2 scope (acceptance test matrix is built/tested from Phase 4 onward)

FILES CREATED:
- docs/system-requirements.md

FILES MODIFIED:
- docs/phase-gate-log.md (this entry)

TESTS:
- None (requirements phase; acceptance criteria defined in section 9 for later phases)

RESULTS:
- 40 functional requirements, 8 scenarios (incl. Bharati-Maitri demo SC-1 and failure
  scenarios SC-4..SC-8), 10 non-functional requirements, 10 acceptance areas

PROBLEMS:
- None

DECISIONS:
- Demo scenario locked as Bharati-Maitri corridor (SC-1), mirroring Mishra et al. 2021
  benchmark where data allow
- No LLM dependency for explanation engine in MVP (FR-29 = COULD, template-based)
- Data footprint rule: heavy data downloaded by script, never committed (NFR-7)

ASSUMPTIONS:
- Vessel profile modeled and flagged as modeled (IN-6); editable per FR-19
- Grid sizes for route domain ~10^4-10^5 cells bound NFR-1 performance targets

VALIDATION:
- Every MUST requirement maps to at least one phase and one acceptance criterion;
  cross-checked against Phase 0 objectives table and Phase 1 gap analysis

PHASE GATE: PASS
```

---
*Next: Phase 3 — Data Strategy (requires team approval).*

---

## PHASE 3 — DATA STRATEGY

```
PHASE:     3 — Data Strategy
STATUS:    COMPLETE (awaiting team approval to begin Phase 4)

COMPLETED:
- Verified (2026-09-05) free-access, open-license sources for every domain: OSI SAF SIC
  (OSI-450/OSI-430-b, CC-BY-4.0), AMSR2 NRT (OSI-408-a), sea-ice drift (OSI-405-c/d),
  ERA5 forcing + waves (CDS, free incl. commercial), GLORYS12 ocean reanalysis
  (CMEMS, 1/12 deg, 1993-present), NSIDC CDR fallback, BYU/NIC + SCAR + US NIC
  iceberg data, GEBCO 2023 (CC-BY-4.0)
- docs/data-strategy.md: 16-product catalog with resolutions, coverage, access, licenses;
  per-domain rationale; Bharati-Maitri curated scenario bundle (box 55-75S/0-95E,
  Dec 2019-Mar 2020 primary, Dec 2022-Mar 2023 extreme) with ~2-4 GB footprint;
  storage layout (raw/processed/scenarios/manifests), scripted fetch plan,
  attribution requirements, public-repo hygiene, provenance requirements (brief §23),
  scope control, assumptions table, references

INCOMPLETE:
- None for Phase 3 scope (downloads + verification happen in Phase 4)

FILES CREATED:
- docs/data-strategy.md

FILES MODIFIED:
- docs/phase-gate-log.md (this entry)

TESTS:
- None (selection/documentation phase; download + QC scripts land in Phase 4)

RESULTS:
- Zero-cost compliance confirmed for every selected product (no paid tiers needed)
- Real iceberg ground truth exists (BYU/NIC daily tracks, SCAR, NIC products); synthetic
  tracks remain a labeled supplement, not a replacement (Phase 1 finding honored)
- Continuous OSI SAF SIC record 1978/79-present (CDR + ICDR) enables persistence-baseline
  ML training and backtests

PROBLEMS:
- None (all license/access claims verified against provider pages)

DECISIONS:
- Primary set: OSI-450+430-b, OSI-405, ERA5 (8 vars, 6-hourly), GLORYS12, iceberg
  catalogs (BYU/NIC + NIC recent), OSI-SAF land mask; GEBCO optional
- Scenario bundle committed as metadata+manifest only; heavy files gitignored (NFR-7)
- Credentials (CDS/CMEMS/Earthdata free accounts) via local env vars, never committed
- Time windows: primary Dec 2019-Mar 2020; extreme Dec 2022-Mar 2023 (record-low ice)

ASSUMPTIONS:
- ERA5 6-hourly sufficient for MVP forcing (hourly if drift errors demand it)
- GLORYS12 daily currents adequate; sub-daily tides ignored in MVP (documented)
- OSI SAF 25 km SIC is training target; 10 km AMSR2 for display

VALIDATION:
- Every selected product mapped to at least one requirement (IN-1..IN-9) and to the
  zero-cost constraint (§7.4); fallback chain defined for ice, forcing, and ocean

PHASE GATE: PASS
```