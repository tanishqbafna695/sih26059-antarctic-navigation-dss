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
- OSI SAF 25 km SIC is training target; 10 km AMSR2 for displayVALIDATION:
- Every selected product mapped to at least one requirement (IN-1..IN-9) and to the
  zero-cost constraint (§7.4); fallback chain defined for ice, forcing, and ocean

PHASE GATE: PASS
```

---
*Next: Phase 4 — Data Pipeline (raw → validation → cleaning → normalization → feature generation → storage). Requires team approval.*

---

## PHASE 4 — DATA PIPELINE

```
PHASE:     4 — Data Pipeline
STATUS:    COMPLETE (awaiting team approval to begin Phase 5)

COMPLETED:
- configs/data_sources.yaml: product registry (all zero-cost) + 2 scenarios
- backend/data_pipeline core: crs (WGS84 <-> EPSG:3412), temporal (daily axes,
  gap fill), grid (common 25 km PS routing grid; rectilinear + polar regridding
  incl. descending-axis handling), qc (missing rate, range checks), features
  (ice mask, edge distance, drift/wind/current store), provenance (manifests)
- fetch clients: era5 (CDS API), cmems (GLORYS12 + OSI SAF SIC/drift),
  icebergs (BYU/NIC + US NIC), gebco (manual); lazy imports, env-var creds
- fetch_all orchestrator: --dry-run (plan + credential status), --synthetic
  (deterministic, credential-free end-to-end), real fetch path
- synthetic.py: labeled SYNTHETIC products (SIC + land mask, drift, ERA5-like,
  GLORYS12-like, advected iceberg tracks) + 7-day bundle generated in repo
- scripts/data_fetch/fetch_all.py CLI wrapper; requirements.txt; pyproject
- tests: 12 passing (CRS, grid, temporal, QC, features, provenance,
  synthetic end-to-end)

INCOMPLETE:
- Real-data download not exercised (needs free CDS/CMEMS accounts + network)
- Land-mask derivation from real OSI SAF status flags (deferred to Phase 6)

FILES CREATED:
- configs/data_sources.yaml, requirements.txt, pyproject.toml, .gitignore
- backend/data_pipeline/ (10 modules), scripts/data_fetch/fetch_all.py
- tests/test_data_pipeline.py, data/manifests/*.json (5 manifests)

FILES MODIFIED:
- docs/phase-gate-log.md (this entry)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 12 passed

RESULTS:
- Synthetic feature store built: sic/drift/era5/glorys12 merged to 7 daily
  timesteps on 175x161 grid (25 km, EPSG:3412); missing rates reported per
  product (21-40% = cells outside the lon/lat box, masked in routing)
- Provenance manifests committed (source, license, res, QC, preprocessing,
  sha256) - data traceability per brief §23
- Public-repo hygiene verified: heavy data + .venv gitignored; only metadata
  committed

PROBLEMS:
- h5netcdf rejects bool dtypes/attrs -> invalid_netcdf=True for internal files,
  int flag for attrs
- RGI only supports trailing extra dims -> moveaxis in regrid_rectilinear
- resample broadcasts static vars onto time axis -> split time/static vars
- glorys synthetic filename mismatch (glorys vs glorys12) -> fixed

DECISIONS:
- One common 25 km EPSG:3412 grid for all routing work; outside-box cells
  stay NaN and are masked in routing (Phase 12)
- Free-account credentials via env vars only; dry-run reports missing creds
- Synthetic products always labeled (attrs + manifests + CSV source column)

ASSUMPTIONS:
- ERA5 6-hourly -> daily means sufficient for the feature store
- OSI SAF/GLORYS product IDs in yaml verified at first real download

VALIDATION:
- 12 tests cover every core module and the credential-free end-to-end path
- .gitignore dry-run staged only code/config/manifests/placeholders

PHASE GATE: PASS
```

---
*Addendum 2026-09-05 — real-data verification (closes the Phase 4 INCOMPLETE item).*

```
STATUS:    REAL-DATA PATH VERIFIED for sic + drift + era5 (see "INCOMPLETE REMAINING")

COMPLETED:
- Real downloads executed with free CDS + CMEMS accounts: OSI SAF SIC
  (39 MB, 106 daily steps), OSI SAF drift (154 MB), ERA5 oper+wave
  (230 MB, 8 variables, 6-hourly)
- Fixed product/dataset ID mismatch: CMEMS `subset()` needs dataset_ids
  (osisaf_obs-si_glo_phy_sic-south_my_amsr_cdr_P1D-m, cmems_obs-si_glo_phy-
  drift-south_my_l4_P1D-m, cmems_mod_glo_phy_my_0.083deg_P1D-m), not the
  product IDs listed in the Phase 3 doc (615a102)
- CDS API URL is now https://cds.climate.copernicus.eu/api (v2 path removed);
  ERA5 requires accepting the Copernicus general licence + dataset licence
- Real files use rectilinear lat/lon grids, native variable names (ice_conc,
  dX_mean/dY_mean, msl) and valid_time dim -> pipeline now auto-detects
  layout and normalizes names/dims
- ERA5 CDS requests split per month (CDS cross-products year x month lists:
  the first download pulled 8 months instead of the 4 in-window ones);
  stream archives merged by interpolation onto the finest grid
- Fetch made idempotent: skips products whose raw file already exists
- Real feature store built: 106 daily steps, 175x161 cells @ 25 km EPSG:3412

INCOMPLETE REMAINING:
- GLORYS12 ocean currents: CMEMS download hung repeatedly at ~2.8 GB (three
  attempts, each killed). NOT in the feature store. Ocean current forcing
  currently uses ERA5 + synthetic fallback; re-attempt later or subset a
  shorter window. Recorded as a data gap, not silently hidden.
- Land-mask derivation from real OSI SAF status flags (Phase 6, unchanged)

TESTS:
- 12/12 passing after all fixes

RESULTS:
- Real SIC seasonal cycle correct: ice-covered fraction 19% (Dec) -> 2% (Mar)
- Real ERA5 physically plausible: u10 -27..19 m/s, t2m 218..280 K, mslp
  95-103 kPa, swh to 8.4 m
- Drift is genuinely sparse in this austral-summer window (<1% cells valid,
  only near the Dec ice band 65-69S): SAR drift needs ice features; the
  Bharati-Maitri corridor is mostly open water by Jan. Data property, not bug.
- Static ~40-56% NaN per product = grid cells outside the native lat/lon box
  (by design, masked in routing)

PROBLEMS:
- CDS 403 "required licences not accepted" -> fixed by accepting the general
  Copernicus licence on the dataset download tab (web UI step)
- ERA5 zip archives + stream splits -> fixed (extract, interp to finest grid,
  merge per month, concat across months)
- GLORYS12 repeated hangs at 2.8 GB (documented above, unresolved)

DECISIONS:
- Real-data gap for the core three products is closed; baseline/ML phases can
  proceed on real SIC/drift/ERA5. GLORYS12 optional (drift forecast benefit).

PHASE GATE: PASS (with documented GLORYS12 gap)
```

---
*Next: Phase 5 — Baselines. Requires team approval.*

---

## PHASE 5 — BASELINES

```
PHASE:     5 — Baselines (FR-6 persistence SIC, FR-9 constant-velocity iceberg,
             FR-21 shortest-path routing)
STATUS:    COMPLETE (awaiting team approval to begin Phase 6)

COMPLETED:
- backend/baselines/: metrics (MAE/RMSE NaN-aware, haversine, position error),
  sea_ice (persistence forecast + per-horizon evaluation), iceberg
  (constant-velocity extrapolation + per-horizon position error),
  routing (navigable-mask Dijkstra over 8-connectivity grid, nearest-valid
  endpoint snapping, no-route reporting)
- scripts/baselines/run_baselines.py: reproducible JSON report under
  data/baselines/ (gitignored; absolute paths never committed)
- evaluation on the REAL 106-day Dec 2019-Mar 2020 feature store

INCOMPLETE:
- Iceberg baseline evaluated on SYNTHETIC tracks only (real BYU/NIC tracks
  not yet downloaded - URL is manual; synthetic tracks labeled per FR-10).
  Re-run with real tracks when available.

FILES CREATED:
- backend/baselines/{__init__,metrics,sea_ice,iceberg,routing,evaluate}.py
- scripts/baselines/run_baselines.py
- tests/test_baselines.py

FILES MODIFIED:
- docs/phase-gate-log.md (this entry), .gitignore (data/baselines/)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 25 passed (12 pipeline + 13 baseline)

RESULTS (recorded run 2026-09-05, data/baselines/latest.json):
- Sea-ice persistence: h=1d MAE 0.0068 / RMSE 0.0300 ... h=5d MAE 0.0208 /
  RMSE 0.0817 (SIC fraction). These are the numbers Phase 6 ML must beat.
- Iceberg constant-velocity (synthetic tracks): mean error 2.94 km @24h,
  5.60 km @48h, 7.88 km @72h. Phase 7 model must beat these.
- Shortest-path Bharati->Maitri on day-0 (2019-12-01) mask: 4247 km over
  143 cells (great-circle = 2331 km; 1.8x = plausible on a coarse 25 km grid
  with ice obstacles + endpoint snapping). Phase 12 routes must improve on
  this at comparable time.

PROBLEMS:
- scipy dijkstra returns 3 values (dist, pred, sources) -> unpacked properly
- 8-connectivity lets routes leak around wall ends -> tests now use
  full-height walls reaching grid edges
- Manifest absolute-path privacy leak found in repo-wide audit -> fixed in
  provenance.py (paths now repo-relative), 13th pipeline test added

DECISIONS:
- Baseline numbers are recorded and frozen as the targets to beat; no ML
  claims until Phase 6/7 runs beat them with recorded logs
- Route endpoints snap to nearest navigable cell (coastal stations sit in
  no-data cells of the 25 km OSI SAF product)

ASSUMPTIONS:
- max_sic=0.8 as the default hard ice-capability obstacle for the baseline
  (vessel-specific limits arrive Phase 11)
- Iceberg constant-velocity baseline uses the last two fixes per berg

VALIDATION:
- 13 baseline unit tests + 1 end-to-end test against the real store;
  recorded run reproducible via scripts/baselines/run_baselines.py

PHASE GATE: PASS
```
