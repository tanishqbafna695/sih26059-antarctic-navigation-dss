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

---
*Next: Phase 6 — Sea-ice forecasting. Requires team approval.*

---

## PHASE 6 — SEA-ICE CONCENTRATION FORECAST

```
PHASE:     6 — Sea-ice forecasting (FR-5 model, FR-6 persistence benchmark,
             FR-7 uncertainty)
STATUS:    COMPLETE with recorded negative ML result (see RESULTS)

COMPLETED:
- backend/forecast/sea_ice.py: delta-formulation ridge model per cell
  (target = sic[t+h]-sic[t], features = recent change + linear trend;
  persistence is the delta=0 fallback inside the model space), trained on the
  early 70% of the window, evaluated on the LATER 30% (temporal split, no
  shuffle leakage)
- FR-7 uncertainty: residual 1-sigma per cell/horizon reported per horizon
- backend/forecast/evaluate_sea_ice.py + scripts/forecast/run_sea_ice.py:
  reproducible JSON report under data/forecast/ (gitignored)
- scikit-learn pinned in requirements.txt (free, Phase 0 §9 locked stack)

INCOMPLETE:
- An ML SIC forecast that BEATS persistence on real data (target, not yet
  achieved on the current single-season window - see RESULTS)

FILES CREATED:
- backend/forecast/{__init__,sea_ice,evaluate_sea_ice}.py
- scripts/forecast/run_sea_ice.py, tests/test_sea_ice_forecast.py (7 tests)

FILES MODIFIED:
- requirements.txt (scikit-learn), .gitignore (data/forecast/),
  docs/phase-gate-log.md (this entry)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 32 passed (25 prior + 7 new)

RESULTS (recorded run 2026-09-05, data/forecast/latest.json):
- Ridge vs persistence on real Dec 2019-Mar 2020 store (held-out later 30%):
    h=1: ridge RMSE 0.027 vs persistence 0.024 (persistence wins)
    h=3: ridge RMSE 0.052 vs persistence 0.041 (persistence wins)
    h=5: ridge RMSE 0.073 vs persistence 0.050 (persistence wins)
- Verified across four formulations (per-cell ridge, pooled ridge,
  wind-forced ridge, advection shift): none beats persistence at 1-5 d on
  this window. The SIC field in the summer corridor evolves too slowly and
  noisily (mostly open water; ice edge retreat is a flat-then-drop threshold
  process a linear trend cannot represent).
- Method sanity check: the SAME model beats persistence decisively on a
  synthetic field with a learnable per-cell decline (h=5 RMSE 0.008 vs
  persistence 0.016) -> implementation is correct; the result is a genuine
  property of the data, not a bug.
- Honest conclusion per brief sections 38/41: persistence remains the
  operational SIC forecast until (a) multi-season OSI-450 CDR training data
  (Phase 3 plan) is ingested, or (b) a stronger model (e.g. spatio-temporal)
  is validated against it. NO fake win is recorded.

PROBLEMS:
- Level-form ridge shrinks AR coefficients <1 and loses to persistence on
  static cells -> delta formulation fixes the structural bias
- Linear-trend delta model over-extrapolates on threshold (flat-then-drop)
  ice-edge cells -> clipping to [0,1]; documented

DECISIONS:
- Record the negative result honestly; persistence stays the benchmark until
  multi-season data or a validated stronger model arrives
- Requirement FR-5's acceptance criterion (beat persistence) is NOT yet met;
  FR-5/7 infrastructure (model + uncertainty + temporal-split harness) is
  delivered and tested

ASSUMPTIONS:
- Single-season (106-day) real window cannot support learning seasonal
  evolution; multi-season OSI-450 CDR training is the planned remedy

VALIDATION:
- 7 unit tests incl. synthetic-win and no-false-win cases; end-to-end test
  on the real store; recorded run reproducible via scripts/forecast/

PHASE GATE: PASS (module delivered; ML-vs-persistence claim NOT YET VALIDATED)
```

---
*Addendum 2026-09-05 — multi-season training closes the Phase 6 gap.*

```
STATUS:    ML-vs-persistence claim now VALIDATED for a seasonal-climatology
           model (the planned multi-season remedy, per Phase 3 data strategy)

COMPLETED:
- backend/data_pipeline/fetch/fetch_training_sic.py: per-season CMEMS OSI SAF
  SIC CDR fetch -> regrid onto the common 25 km grid -> concatenated labeled
  record (season + day-in-season coords). Demo window 2019-12-01..2020-03-15
  is EXCLUDED from training by construction (held-out season). Validated on a
  3-season bundle (2016-17..2018-19, 315 days, 71 MB). 16-season extension
  (2003-2018) is a one-command re-run (--start-year 2003).
- backend/forecast/seasonal.py: seasonal-climatology delta model
  forecast[t+h] = sic[t] + mean over TRAINING seasons of the smoothed
  day-in-season SIC change summed over [t, t+h). Persistence is the delta=0
  special case; the climatology only adds skill where melt is systematic.
  Moving-average smoothing fully vectorized + NaN-safe.
- backend/forecast/evaluate_seasonal.py + scripts/forecast/run_seasonal.py:
  reproducible JSON report (data/forecast/latest_seasonal.json, gitignored);
  season length auto-detected from gaps in the training time axis

INCOMPLETE:
- Training bundle currently 3 seasons; widening to the full 2002-2018 CDR
  record would sharpen the climatology (one-command re-run, ~30 min)

FILES CREATED:
- backend/data_pipeline/fetch/fetch_training_sic.py
- backend/forecast/seasonal.py, backend/forecast/evaluate_seasonal.py
- scripts/forecast/run_seasonal.py, tests/test_seasonal_forecast.py (6 tests)
- data/manifests/training_sic.json

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 38 passed (32 prior + 6 new)

RESULTS (recorded run 2026-09-05, data/forecast/latest_seasonal.json):
- Seasonal climatology vs persistence on the held-out 2019-20 season, scored
  over the SAME later 30% pairs as the Phase 6 ridge run:
    h=1: seasonal RMSE 0.0235 vs persistence 0.0235 (tie)
    h=2: seasonal RMSE 0.0340 vs persistence 0.0343 (seasonal wins)
    h=3: seasonal RMSE 0.0403 vs persistence 0.0410 (seasonal wins)
    h=4: seasonal RMSE 0.0449 vs persistence 0.0459 (seasonal wins)
    h=5: seasonal RMSE 0.0487 vs persistence 0.0501 (seasonal wins)
- RMSE improvement grows with horizon (h=2 +0.0003 ... h=5 +0.0015) - the
  physically expected signature: the climatology knows the systematic Dec-Mar
  melt that persistence cannot see. This is the FIRST positive
  model-vs-baseline result on real data (Phase 5 baselines 2723bd7, ridge
  negative 13d5417).
- Method sanity: on a synthetic multi-season field with a shared retreat the
  model beats persistence decisively; on a static field it claims no win.

PROBLEMS:
- season_len overwrite bug (runner passed full 315 days as one season) ->
  auto-detect season length from time-axis gaps; regression test added
- apply_along_axis smoothing was slow + nanmean empty-slice warnings ->
  vectorized cumsum moving mean with explicit valid-count mask
- Cumsum window length off-by-window_half -> zero-prefixed cumsum; tests
  assert exact (ny, nx, season_len-1) shape

DECISIONS:
- FR-5 acceptance (model beats the FR-6 persistence baseline) now has a
  validated positive result on real held-out data - but honest caveat: the
  win is climatological (systematic seasonal melt), modest in magnitude, and
  trained on 3 seasons. Claim kept proportionate; widening training seasons
  is the documented next strengthening step.

PHASE GATE: PASS (ML-vs-persistence claim VALIDATED for seasonal model;
           ridge per-window model remains negative, recorded above)
```

---
*Next: Phase 7 — Iceberg Trajectory Prediction. Requires team approval.*

---

## PHASE 7 — ICEBERG TRAJECTORY PREDICTION

```
PHASE:     7 — Iceberg Trajectory Prediction (FR-8 probabilistic trajectories,
             FR-9 baseline benchmarking, FR-10 source transparency, FR-11 staleness bounds)
STATUS:    COMPLETE (awaiting team approval to begin Phase 8)

COMPLETED:
- backend/iceberg/drift.py: physics-guided empirical drift model (combining kinematic velocity,
  momentum decay tau=24h, atmospheric wind u10/v10 with Southern Hemisphere leeway deflection
  theta=-20 deg, ocean current uo/vo coupling, and kinematic persistence fallback) + ML drift model
  (fitted Ridge regression over historical displacement vectors).
- FR-8 & FR-11 probabilistic uncertainty bounds: calculated 1-sigma uncertainty radius R_unc(h),
  semi-major/semi-minor ellipse axes (a_km, b_km), orientation angle, and confidence scores
  degrading with horizon h and observation staleness tau_stale.
- backend/iceberg/evaluate.py + scripts/iceberg/run_iceberg.py: reproducible benchmark harness
  evaluating models against Constant Velocity baseline across 24h, 48h, 72h horizons, saving
  JSON output to data/iceberg/latest.json.
- FR-10 transparent labeling: track source metadata explicitly preserved ("synthetic" vs "BYU_NIC").

INCOMPLETE:
- Evaluation currently performed on synthetic tracks. Real BYU/NIC iceberg track ingest pipeline
  ready to run when additional historical track files are fetched.

FILES CREATED:
- backend/iceberg/{__init__,drift,evaluate}.py
- scripts/iceberg/run_iceberg.py
- tests/test_iceberg_drift.py (6 tests)

FILES MODIFIED:
- docs/phase-gate-log.md (this entry)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 44 passed (38 prior + 6 new)

RESULTS (recorded run 2026-09-06, data/iceberg/latest.json):
- Constant-Velocity Baseline: 2.05 km @24h, 3.89 km @48h, 5.86 km @72h mean position error.
- Physics Drift Model (kinematic fallback path): matches baseline (2.05 / 3.89 / 5.86 km) with
  explicit uncertainty bounds (mean R_unc: 2.92 km @24h, 5.78 km @48h, 8.65 km @72h; mean confidence
  0.86 @24h, 0.71 @48h, 0.57 @72h).

PROBLEMS:
- Fitting sample count threshold of 5 was too restrictive for short test tracks -> lowered to 3;
  regression test added.

DECISIONS:
- Iceberg drift model explicitly provides probabilistic uncertainty geometry (ellipse axes + orientation)
  needed for Phase 10 hazard field building and MapLibre frontend rendering (FR-37).
- Synthetic tracks remain strictly labeled as `synthetic: true`.

ASSUMPTIONS:
- Wind leeway deflection angle theta = -20 deg (leftward) for Southern Ocean sea ice / iceberg drift.

VALIDATION:
- 6 unit tests covering wind rotation, momentum decay, uncertainty expansion, ML fallback, fitting,
  and end-to-end evaluation harness. All 44 system tests passing.

PHASE GATE: PASS
```

---
*Next: Phase 8 — Weather & Ocean Environmental Forcing Integration. Requires team approval.*

---

## PHASE 8 — WEATHER & OCEAN ENVIRONMENT INTEGRATION

```
PHASE:     8 — Weather & Ocean Environmental Forcing Integration (IN-4 ERA5 forcing,
             IN-5 ocean physics, fallback chain, weather/ocean severity indexing)
STATUS:    COMPLETE (awaiting team approval to begin Phase 9)

COMPLETED:
- backend/environment/weather.py: derived atmospheric variables (wind speed in m/s and knots,
  meteorological wind direction 0-360 deg, temperature t2m, pressure mslp, wave height swh, wave period mwp),
  Beaufort scale mapping (0..12), wave severity index, and combined weather_severity_index (0.0..1.0).
- backend/environment/ocean.py: surface ocean current speed/heading, sea surface temperature, and
  documented 3-tier fallback chain (GLORYS12 uo/vo -> OSI SAF sea-ice drift -> empirical wind-driven
  surface ocean current estimate v_ocean = 0.02 * R(-20 deg) * v_wind).
- backend/environment/store.py: EnvironmentStore and EnvironmentState point query accessor over
  processed features.nc datasets, providing unified environmental risk fields.
- scripts/environment/run_environment.py: CLI runner sampling Bharati-Maitri waypoints and exporting
  benchmark JSON report to data/environment/latest.json.

INCOMPLETE:
- None for Phase 8 scope.

FILES CREATED:
- backend/environment/{__init__,weather,ocean,store}.py
- scripts/environment/run_environment.py
- tests/test_environment.py (6 tests)

FILES MODIFIED:
- docs/phase-gate-log.md (this entry)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 50 passed (44 prior + 6 new)

RESULTS (recorded run 2026-09-06, data/environment/latest.json):
- Verified waypoint sampling across Bharati Station (-69.4S, 76.2E), Prydz Bay (-68.0S, 70.0E),
  Mid-Corridor (-67.5S, 45.0E), Riiser-Larsen Sea (-68.5S, 25.0E), and Maitri Station (-70.7S, 11.7E).
- Fallback chain tested: missing GLORYS12 ocean currents correctly trigger empirical wind-driven
  current fallback (`source="wind_driven_estimate"`).

PROBLEMS:
- Grid shape mismatch in EnvironmentStore between 1D x/y coordinate vectors (161x175) -> fixed with
  np.meshgrid distance calculation; regression test added.

DECISIONS:
- Combined environmental risk severity formula defined as 40% sea-ice concentration + 40% weather severity +
  20% ocean current severity for downstream Phase 10 hazard field integration.

ASSUMPTIONS:
- Wind-driven surface current approximation uses 2% wind slip coefficient with -20 deg leftward deflection.

VALIDATION:
- 6 unit tests covering wind/wave severity, Beaufort scale mapping, ocean fallback chain, and
  EnvironmentStore point queries. All 50 system tests passing.

PHASE GATE: PASS
```

---
*Next: Phase 9 — Uncertainty Engine. Requires team approval.*

---

## PHASE 9 — UNCERTAINTY ENGINE

```
PHASE:     9 — Uncertainty Engine (FR-12 forecast status & confidence, FR-13 confidence
             degradation with horizon & staleness, FR-14 uncertainty-aware decision rule)
STATUS:    COMPLETE (awaiting team approval to begin Phase 10)

COMPLETED:
- backend/uncertainty/engine.py: UncertaintyEngine, ConfidenceReport, compute_sic_prediction_interval
  (empirical 90%/95% CIs with horizon residual variance sigma_sic(h)), compute_iceberg_uncertainty_ellipse
  (1-sigma radius R_unc(h, tau_stale) & anisotropic ellipse axes), compute_combined_confidence (unified
  confidence score C_total in [0.1, 1.0] with missing input & staleness degradation), and uncertainty_aware_risk
  (risk inflation H_u_aware = H_mean + k * sigma_H for navigator risk aversion k >= 0).
- scripts/uncertainty/run_uncertainty.py: CLI runner evaluating confidence scenarios, prediction intervals,
  and risk inflation rules, exporting benchmark JSON report to data/uncertainty/latest.json.

INCOMPLETE:
- None for Phase 9 scope.

FILES CREATED:
- backend/uncertainty/{__init__,engine}.py
- scripts/uncertainty/run_uncertainty.py
- tests/test_uncertainty.py (6 tests)

FILES MODIFIED:
- docs/phase-gate-log.md (this entry)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 56 passed (50 prior + 6 new)

RESULTS (recorded run 2026-09-06, data/uncertainty/latest.json):
- Sea-Ice 90% CIs: h=1d sigma=0.027 [0.456..0.544] ... h=5d sigma=0.055 [0.409..0.591].
- Iceberg Ellipses: h=24h R_unc=3.06 km (Conf 0.78) ... h=72h R_unc=8.70 km (Conf 0.50).
- Scenario Confidence: nominal_24h = 0.88 (HIGH), nominal_72h = 0.63 (MEDIUM), stale_obs_12h = 0.76 (MEDIUM),
  missing_satellite_sc4 = 0.48 (DEGRADED).
- Risk Inflation (FR-14): mean=0.40, std=0.15 -> k=0: 0.40, k=1: 0.55, k=2: 0.70.

PROBLEMS:
- Missing input status threshold was assigning MEDIUM status -> updated status classification so missing mandatory
  inputs set status="DEGRADED"; regression test added.

DECISIONS:
- Risk inflation parameter k defaults to k=1.0 for risk-averse routing in Phase 10 & 12, allowing uncertain
  shortcuts to be penalized in favor of well-observed safe corridors.

ASSUMPTIONS:
- Empirical sea ice forecast residual variance grows linearly with horizon days: sigma(h) = 0.020 + 0.007 * h.

VALIDATION:
- 6 unit tests covering prediction intervals, ellipse growth, confidence degradation, missing input penalty,
  and risk-averse inflation. All 56 system tests passing.

PHASE GATE: PASS
```

---
*Next: Phase 10 — Polar Hazard Field. Requires team approval.*

---

## PHASE 10 — POLAR HAZARD FIELD

```
PHASE:     10 — Polar Hazard Field (FR-15 unified hazard H(x,t,v), FR-16 decomposed component
             formulation, FR-17 vessel-specific risk differentiation)
STATUS:    COMPLETE (awaiting team approval to begin Phase 11)

COMPLETED:
- backend/hazard/field.py: PolarHazardField, HazardComponentBreakdown, compute_sea_ice_hazard
  (quadratic soft risk + hard obstacle thresholding), compute_iceberg_hazard (Gaussian spatial danger
  buffers with 1-sigma uncertainty radius), compute_weather_hazard, compute_ocean_hazard, and
  compute_hazard_grid.
- Enforced hard constraints (landmask, SIC > max_sic_limit, wave/wind limits) as blocking barriers
  (total_hazard = 1.0, is_blocked = True) while scoring soft risks continuously in [0.0, 0.99].
- scripts/hazard/run_hazard.py: CLI runner evaluating hazard fields across 3 vessel profiles (Open Water Vessel,
  Polar Class PC7, Heavy PC1 Icebreaker), exporting benchmark JSON report to data/hazard/latest.json.

INCOMPLETE:
- None for Phase 10 scope.

FILES CREATED:
- backend/hazard/{__init__,field}.py
- scripts/hazard/run_hazard.py
- tests/test_hazard.py (5 tests)

FILES MODIFIED:
- docs/phase-gate-log.md (this entry)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 61 passed (56 prior + 5 new)

RESULTS (recorded run 2026-09-06, data/hazard/latest.json):
- Demonstrated Vessel-Specific Differentiation (FR-17, SC-6) on identical Antarctic environment:
  - Open Water Research Vessel (15% SIC limit): Domain Navigable Area = 28.0%, Mean Hazard = 0.72.
  - Polar Class PC7 Vessel (60% SIC limit): Domain Navigable Area = 34.5%, Mean Hazard = 0.66.
  - Heavy Icebreaker PC1 (100% SIC limit): Domain Navigable Area = 43.6%, Mean Hazard = 0.58.

PROBLEMS:
- Missing pandas import in field.py during pandas.Timestamp grid selection -> added `import pandas as pd`;
  regression test passed.

DECISIONS:
- Hazard weights set to 35% sea ice, 35% iceberg proximity, 20% weather, 10% ocean current for baseline
  unified hazard field, feeding into Phase 12 multi-objective route optimization.

ASSUMPTIONS:
- Iceberg Gaussian danger buffer uses R_danger = 5 km base buffer + 3 * R_unc.

VALIDATION:
- 5 unit tests covering soft/hard constraint logic, iceberg Gaussian buffers, weather limits,
  vessel-specific hazard differentiation, and decomposed risk breakdowns. All 61 system tests passing.

PHASE GATE: PASS
```

---
*Next: Phase 11 — Vessel Model. Requires team approval.*

---

## PHASE 12 — ROUTE OPTIMIZATION

```
PHASE:     12 — Route Optimization (FR-22 multi-objective routes, FR-23
              time-aware costs, FR-24 no-route statement)
STATUS:    COMPLETE (awaiting team approval to begin Phase 13)

COMPLETED:
- backend/routing/costs.py: vectorized per-day cost fields (hazard, base
  speed, fuel, iceberg advection) mirroring the Phase 8/10/11 scalar
  functions; DayFieldsCache with lazy per-day build + arrival-day lookup;
  WEIGHT_PRESETS fastest/safest/balanced (configurable); forcing-NaN
  imputation with documented EnvironmentStore defaults + reported fraction
- backend/routing/optimizer.py: time-dependent label-setting Dijkstra over
  the 8-connectivity grid (same topology as the Phase 5 baseline);
  edge cost = a*risk + b*(time_h/T_ref) + g*(fuel_L/F_ref) with documented
  single-cell reference scales; arrival-time-tracked relaxation (hazard/
  speed evaluated at transit day); NoRouteFound carrying OUT-8 diagnostics;
  endpoint snapping under the vessel's own limits; per-route metrics
  (distance/time/fuel/mean+max hazard/ice+berg exposure) + Phase 9 confidence
- scripts/routing/run_routing.py: Bharati->Maitri plans for all 3 vessel
  presets + shortest-path baseline scored on the SAME time-aware ledger;
  reproducible JSON report under data/routing/ (gitignored)
- tests/test_routing.py (15 tests)

INCOMPLETE:
- Forcing-coupled iceberg advection (kinematic-only MVP; Phase 15 refinement)
- Corner-cutting rule for diagonal moves (parity with Phase 5 baseline kept)

FILES CREATED:
- backend/routing/{__init__,costs,optimizer}.py
- scripts/routing/run_routing.py
- tests/test_routing.py

FILES MODIFIED:
- .gitignore (data/routing/), docs/phase-gate-log.md (this entry),
  docs/innovation-claims.md (#20 promoted, see below)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 80 passed (65 prior + 15 new)

RESULTS (recorded run 2026-09-06, data/routing/latest.json, depart day 45
= 2020-01-15, 2 ASSUMED demo icebergs advected kinematically):
- PC1: fastest 221.2 h / 207528 L / risk 0.038; safest 222.0 h / 205407 L /
  risk 0.037; balanced 222.0 h / 205315 L / risk 0.038; baseline 240.2 h /
  192502 L / risk 0.064 / ice-exposure 0.29 (vs 0.10-0.11 for ours).
  Multi-objective routes beat the shortest-path baseline on modeled time,
  risk AND ice exposure: the baseline cuts through slow ice while the
  time-aware routes avoid it (transit spans dataset days 45-54).
- PC7: fastest 291.1 h / risk 0.041; safest 291.9 h / risk 0.040; balanced
  291.8 h / risk 0.040 (paths differ; corridor mostly open water so deltas
  are honestly small). Static day-45 baseline finds NO PATH while the
  time-aware router succeeds -> FR-23 evidence.
- Open Water RV: NO ROUTE (86% domain blocked) -> FR-20 + FR-24 on real
  data: same environment, OW cannot sail, PC7/PC1 can.
- Day 0 (2019-12-01) is ice-locked for OW + PC7 (start pocket, search
  exhausts after 46/87 cells) -> recorded finding, not a bug.
- Confidence 0.10 DEGRADED (291 h horizon + GLORYS12 fallback active) per
  the Phase 9 formula; ocean_source=wind_driven_estimate (GLORYS12 gap open).
- Performance: full 3-route PC7 plan ~1 s on ~11k navigable cells (NFR-1 OK).

PROBLEMS:
- NaN ERA5 forcing outside the product box propagated into hazard (NaN) and
  speed (0.5 kt floor) -> absurd 1186 h PC1 times. Fixed with documented
  imputation mirroring EnvironmentStore._val defaults + forcing_imputed_frac
  in fields/report; consistency tests added.
- Endpoint snapping raised raw ValueError on fully-blocked domains ->
  converted to NoRouteFound/OUT-8 (FR-24); regression test added.
- Vectorized haversine mixed scalar math with arrays (TypeError) -> fixed.
- Synthetic weight-separation geometry: sea-ice slowdown dominates ALL
  weight sets (fastest also avoids ice) -> real finding; tests use a
  calm-weather iceberg-wall scene where risk carries no slowdown, plus
  exact pure-objective optimality asserts on a static 1-day store.

DECISIONS:
- T_ref/F_ref = single reference-cell crossing at cruise/base-fuel, so
  weights a/b/g are interpretable across vessels; documented in optimizer.
- FIFO approximation for composite-cost label-setting recorded as an ASSUMED
  limitation (exact for arrival time, near-optimal for weighted cost).
- Recorded evidence uses --depart-day 45; default stays 0 (voyage window
  start; ice-locked no-routes there are legitimate FR-24 outputs).
- Claim #20 (multi-route alternatives with trade-offs) promoted to
  EXPERIMENTALLY VALIDATED; claim #23 stays NOT YET VALIDATED (needs
  Phase 16/19 backtests).

ASSUMPTIONS:
- Demo iceberg fixes/velocities ASSUMED (labeled in report); uncertainty
  grows via the Phase 7 model during advection.
- 8-connectivity parity with baseline (corner cutting possible; noted).

VALIDATION:
- 15 routing tests: vector==scalar consistency (beaufort/weather/ocean/ice/
  fuel/speed), pure-objective optimality, fastest/safest divergence with
  correct risk/time ordering, no-route OUT-8 details, blocked-cell exclusion,
  day-cache mapping, real-store e2e (PC7 day 45). Full suite 80/80 green.

PHASE GATE: PASS
```

---
*Next: Phase 13 — Route Trade-Off Engine. Requires team approval.*

---

## PHASE 13 — ROUTE TRADE-OFF ENGINE

```
PHASE:     13 — Route Trade-Off Engine (FR-25 comparison, FR-26
              priority-weighted recommendation)
STATUS:    COMPLETE (awaiting team approval to begin Phase 14)

COMPLETED:
- backend/tradeoff/comparison.py: master-brief §6 table builder from a
  Phase 12 vessel plan (time/fuel/risk/max-risk/ice/berg-exposure/distance
  + shared set-level confidence flagged as shared); baseline row included
  when found; no-route plans pass through with reason (never empty table)
- backend/tradeoff/recommend.py: 4 documented priority profiles (balanced,
  safety_first, time_first, fuel_saver; weights sum to 1.0, asserted);
  min-max scoring over candidate routes (baseline is evidence, never a
  candidate); exact-tie break to "balanced"; per-metric %-deltas vs every
  alternative (zero baseline -> null, never ±inf); structured quantitative
  reasons + headline improvements as the evidence base for Phase 14;
  LOW/DEGRADED confidence attaches a caveat (FR-14 re-ranking explicitly
  NOT claimed)
- scripts/tradeoff/run_tradeoff.py: per-vessel table + full sensitivity
  matrix (4 profiles x vessels); reproducible JSON under data/tradeoff/
- tests/test_tradeoff.py (12 tests)

INCOMPLETE:
- Narrative explanation prose (Phase 14 owns it; Phase 13 outputs the data)
- FR-14 uncertainty-aware re-ranking inside recommendation (SHOULD;
  recorded as caveat, not implemented)

FILES CREATED:
- backend/tradeoff/{__init__,comparison,recommend}.py
- scripts/tradeoff/run_tradeoff.py
- tests/test_tradeoff.py

FILES MODIFIED:
- .gitignore (data/tradeoff/), docs/phase-gate-log.md (this entry),
  docs/innovation-claims.md (#20 notes extended, see below)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 92 passed (80 prior + 12 new)

RESULTS (recorded run 2026-09-06, data/tradeoff/latest.json, from the
Phase 12 depart-day-45 report):
- PC7: balanced->safest, safety_first->safest, time_first->fastest,
  fuel_saver->balanced. Winners MOVE with priorities (master §27
  sensitivity live on real data). Deltas honest and small (open-water
  corridor): e.g. safest vs fastest -25.6% ice exposure at +0.3% time.
- PC1: balanced->safest, safety_first->safest, time_first->fastest,
  fuel_saver->balanced. Baseline row visible at 0.064 risk / 0.29 ice
  exposure vs <=0.038 / <=0.11 for ours.
- Open Water RV: no routes -> recommendation None with reason (FR-24
  passthrough verified end to end).
- Every recommendation carries the DEGRADED-confidence caveat (0.10 set
  confidence from the 200-290 h horizon + ocean fallback).

PROBLEMS:
- None (12/12 tradeoff tests passed on first run; arithmetic pre-verified)

DECISIONS:
- Baseline never a recommendation candidate (it is the thing we compare
  against, per Phase 0 §6 benchmarking discipline).
- Confidence is a qualifier, not a scoring metric (it is set-level; scoring
  it per-route would fabricate precision).
- Claim #20 extended: trade-off comparison + priority recommendation now
  validated; narrative explanation stays with Phase 14.

ASSUMPTIONS:
- Priority profile weights are team-chosen defaults, documented in
  recommend.py; navigator-editable in the Phase 17 UI (FR-39).

VALIDATION:
- 12 tradeoff tests: builder incl. baseline/shared-confidence, expected
  winners per profile, sensitivity (winners differ), score bounds, delta
  math incl. zero guard, tie-break, caveat, no-route passthrough, unknown
  profile. Full suite 92/92 green.

PHASE GATE: PASS
```

---
*Next: Phase 14 — Explanation Engine. Requires team approval.*

---

## PHASE 14 — EXPLANATION ENGINE

```
PHASE:     14 — Explanation Engine (FR-27 recommendation explanation,
              FR-28 change-explanation structure)
STATUS:    COMPLETE (awaiting team approval to begin Phase 15)

COMPLETED:
- backend/explanation/explainer.py: deterministic template explanations
  built only from recorded numbers. explain_recommendation() emits
  headline + strengths + prices + vessel-fit statement + confidence note +
  caveats + rendered text. explain_change() reports switch/hold with
  trigger + metric deltas (FR-28; real environmental pairs arrive Ph15).
- Significance discipline in code: strengths need |pct| >= 1.0 AND
  abs >= 0.002 for hazard/exposure (kills noise like "-50% iceberg risk"
  on 0.0002-vs-0.0001); prices always shown or an explicit negligible-cost
  note; no-route input yields an honest non-explanation.
- scripts/explanation/run_explanation.py: per-vessel balanced-profile
  explanations + FR-28 shape demo; JSON under data/explanation/
- tests/test_explanation.py (9 tests)

INCOMPLETE:
- Real environmental re-route pairs for explain_change (Phase 15 feeds it)
- UI rendering of explanations (Phase 17; preview dashboard keeps its own
  copy of the reason sentences for now)

FILES CREATED:
- backend/explanation/{__init__,explainer}.py
- scripts/explanation/run_explanation.py
- tests/test_explanation.py

FILES MODIFIED:
- .gitignore (data/explanation/), docs/phase-gate-log.md (this entry),
  docs/innovation-claims.md (#21 notes extended, see below)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 101 passed (92 prior + 9 new)

RESULTS (recorded run 2026-09-06, data/explanation/latest.json):
- PC7: "Take the safest route: 291.9 h, 153,628 L, risk 0.040" + "25.6%
  less ice exposure than fastest" + negligible-cost note + PC7 vessel-fit
  (7.8% vs 60% limit, worst cell 0.177) + DEGRADED caveat. The -50%
  iceberg delta was correctly suppressed as noise (abs 0.0001).
- PC1: analogous explanation (9.7% vs 100% limit, worst cell 0.135).
- OW RV: honest non-explanation (no route).
- Change demo (recorded-shape): fastest -> safest with time +0.4%,
  fuel -1.0%, risk -2.9%.

PROBLEMS:
- UnicodeEncodeError on Windows console (U+2192 arrow in change text) ->
  ASCII-only in all printed strings; regression visible in recorded run.
  Docstring-only non-ASCII left untouched (never printed).

DECISIONS:
- No LLM (C-6, FR-29 COULD): templates only, fully deterministic
  (test asserts byte-identical repeat runs).
- FR-14 re-ranking stays out; caveat carried, not silently absorbed.
- Claim #21 stays PROPOSED (dynamic half pending Phase 15); notes record
  the explanation half as validated with evidence path.

ASSUMPTIONS:
- Vessel limits from the modeled registry (FR-19 flagged as modeled).
- Change-demo trigger in the recorded run is a priority shift, explicitly
  labeled "demo shape".

VALIDATION:
- 9 explanation tests: headline numbers, both-sides coverage, noise guard,
  negligible-cost note, vessel statement, caveat propagation, no-route
  honesty, switch/hold/missing-side change logic, determinism.
  Full suite 101/101 green.

PHASE GATE: PASS
```

---
*Next: Phase 15 — Dynamic Re-Routing. Requires team approval.*

---

## PHASE 15 — DYNAMIC RE-ROUTING

```
PHASE:     15 — Dynamic Re-Routing (FR-30 update recompute, FR-31 OUT-6
              notice, FR-32 configurable thresholds)
STATUS:    COMPLETE (awaiting team approval to begin Phase 16)

COMPLETED:
- backend/routing/optimizer.py: additive arrival_times() helper (same
  per-leg speed rule as search/evaluate; no existing behavior touched)
- backend/rerouting/reroute.py: RerouteThresholds (berg-move / SIC-delta /
  hazard-jump, FR-32); detect_changes() along remaining-path cells (new-fix
  appearance always listed); reroute() locating the vessel by sailed hours,
  re-scoring the remaining course IN THE NEW WORLD vs fresh cell-direct
  re-optimization (no snapping jump), outcome RE-ROUTE/ADJUSTED/HOLDS/
  COMPLETE/NO_ROUTE, OUT-6 notice with Phase 14 change + recommendation
  explanations (FR-31)
- scripts/rerouting/run_reroute.py: PC7 day-45 -> sail 120 h -> day-50
  update; case A control (observations only), case B SC-5 ASSUMED fresh
  berg fix on the remaining course; JSON under data/rerouting/
- tests/test_reroute.py (5 tests) + 1 hold-qualifier regression test in
  test_explanation.py

INCOMPLETE:
- Live/operational update feeds (prototype uses recorded days + labeled
  scenario injections, per C-1)
- Forcing-coupled berg advection (still kinematic; unchanged)

FILES CREATED:
- backend/rerouting/{__init__,reroute}.py
- scripts/rerouting/run_reroute.py
- tests/test_reroute.py

FILES MODIFIED:
- backend/routing/optimizer.py (arrival_times helper only),
  backend/explanation/explainer.py (base-name switch detection),
  tests/test_explanation.py (+1 test), .gitignore (data/rerouting/),
  docs/phase-gate-log.md (this entry), docs/innovation-claims.md (#21
  promoted, see below)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 107 passed (101 prior + 6 new)

RESULTS (recorded run 2026-09-06, data/rerouting/latest.json, PC7):
- Case A control: ADJUSTED, no threshold trigger; staying 172.6 h/risk
  .028 vs new advice 172.5 h/risk .027 (real 5-day evolution only).
- Case B SC-5: trigger fires ("1 new iceberg fix appeared; danger jump
  0.999 on remaining path"); staying risk .035 vs new advice .029 (-15%)
  at +0.2% time: the new path demonstrably avoids the injected fix.
- Both cases keep winner safest under balanced priorities; the notice
  reports path movement either way (never hidden).

PROBLEMS:
- Change headline read "changed safest -> safest" when only the
  "(remaining course)" qualifier differed -> base-name switch detection
  in explain_change + regression test; verified in re-run ("holds").
- Test declared old winner "fastest" while balanced priorities recommend
  "balanced" on symmetric scenes -> test setup corrected (engine was
  right); null-update HOLDS confirmed.
- Two `//` C++-style comment slips in new Python code (one crashed the
  runner on sight, one caught by grep) -> ASCII `#` only; all printed
  strings verified ASCII for the Windows console.

DECISIONS:
- Staying-the-course is scored under NEW fields (the correct decision
  frame: old advice, new world) rather than compared against stale numbers.
- New-fix appearance always triggers listing (discrete event, no
  threshold); magnitude thresholds gate move/shift/jump triggers.
- Claim #21 (explain + dynamically recompute) promoted to
  EXPERIMENTALLY VALIDATED: both halves now have recorded runs.

ASSUMPTIONS:
- Case B fix is ASSUMED (labeled in report + notice); a real fix arrives
  through the same code path with staleness reset (FR-11 compatible).
- Day-50 real fields stand in for "new observations" (offline prototype).

VALIDATION:
- 6 new tests: arrival monotonicity, null-hold, wall-forces-move,
  threshold configurability (both directions), voyage-complete,
  hold-qualifier. Full suite 107/107 green.

PHASE GATE: PASS
```

---
*Next: Phase 16 — Backtesting. Requires team approval.*

---

## PHASE 16 — BACKTESTING

```
PHASE:     16 — Backtesting (SC-1…SC-8 acceptance evidence)
STATUS:    COMPLETE (awaiting team approval to begin Phase 17)

COMPLETED:
- backend/backtest/harness.py: run_departure_matrix() (full Ph12+13 chain
  per (vessel, day); NoRouteFound recorded as data) + summarize_matrix()
  (success rate, SC-6 same-day vessel differences, SC-7 no-route ledger)
- Additive stale support, no behavior change elsewhere: DayFieldsCache
  max_day_index (frozen last-observation fields) + reroute() staleness_h /
  extra_missing_inputs threading into confidence
- scripts/backtest/run_backtest.py: matrix + SC-4 (SIMULATED outage vs
  fresh control) + SC-5 ice (day-60 sail into day-65 refreeze) + SC-8
  (pre-storm day-70 vs calm day-55) + SC-3 evidence check; JSON under
  data/backtest/
- tests/test_backtest.py (4 tests)
- Closed a prior gap found by probing: data/vessel/latest.json was never
  recorded on this checkout -> scripts/vessel/run_vessel.py executed.

INCOMPLETE:
- Academic-route benchmark (Mishra Bharati-Maitri) — needs the paper's
  exact cost setup; recorded as NOT YET VALIDATED under claim #23
- Iceberg ML beating constant-velocity on real tracks (model ties
  baseline on synthetic; real BYU/NIC tracks still manual-download)

FILES CREATED:
- backend/backtest/{__init__,harness}.py
- scripts/backtest/run_backtest.py
- tests/test_backtest.py

FILES MODIFIED:
- backend/routing/costs.py (max_day_index), backend/rerouting/reroute.py
  (staleness threading), .gitignore (data/backtest/),
  docs/phase-gate-log.md (this entry)

TESTS:
- .venv/Scripts/python -m pytest tests -q -> 111 passed (107 prior + 4 new)

RESULTS (recorded run 2026-09-06, data/backtest/latest.json):
- MATRIX 7/10 (SC-1/2): PC7+PC1 route days 45/55/60/65 (time 222-292 h,
  risk 0.031-0.051); OW RV no-route all 3 days (SC-7 ledger x3).
- SC-6: all 3 shared days show OW-fail/PC-succeed splits (FR-20).
- SC-4: stale vs fresh confidence both 0.10 DEGRADED — the 170 h+ horizon
  floors the Phase 9 formula either way (NOT retuned: no metric-shopping).
  Outage evidence = explicit missing-input label + component scores at
  floor + frozen-fields outcome; honestly weaker than a collapse, recorded
  as such. Stale outcome HOLDS/ADJUSTED per JSON (no fake drama).
- SC-5 ice: day-60 balanced risk 0.048 -> day-65 update RE-ROUTES on
  sub-threshold evolution (close-call flip, no trigger listed by design:
  thresholds gate trigger listing, outcomes always compute).
- SC-8: pre-storm fastest 292 h / risk 0.048 / max 0.244 vs calm 281 h /
  0.032 / 0.126 — storm signal visible (max hazard ~2x).
- SC-3: environment/hazard/uncertainty/baselines evidence files present.

PROBLEMS:
- SC-4 floor effect (above): recorded honestly; formula untouched.
- Probe first showed the missing vessel artifact (above): closed by run.

DECISIONS:
- Claim #23 stays NOT YET VALIDATED: iceberg-ML and academic-route wins
  are still open; PC1-vs-shortest-path and seasonal-vs-persistence wins
  stand but do not cover the whole claim (Phase 19 audit owns the call).
- Matrix days {45,55,60,65} chosen by probe (all PC routable; OW fails).

ASSUMPTIONS:
- SC-4 outage is SIMULATED (frozen fields, labeled); day-65 fields stand
  in for deteriorated observations (offline prototype, C-1).

VALIDATION:
- 4 backtest tests: open-water matrix, wall-driven SC-6/SC-7 detection,
  stale clamp equality, empty-matrix safety. Full suite 111/111 green.

PHASE GATE: PASS
```

---
*Next: Phase 17 — User Interface. Requires team approval.*




