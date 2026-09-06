# Innovation Claim Ledger — SIH26059

**Phase:** 19 · **Promotions 2026-09-06:** claim #20 → EXPERIMENTALLY VALIDATED (Phase 12/13), claim #21 → EXPERIMENTALLY VALIDATED (Phase 15), claim #19 → EXPERIMENTALLY VALIDATED (Phase 10/18)
**Last updated:** 2026-09-06 (Phase 19 audit)

Every claim about our system or about others is logged with a status class and evidence. **A claim is never promoted to a higher class without evidence.** Rules:
- **VERIFIED** — supported by a primary source we read (operator statement, paper, official page).
- **INFERRED** — reasonable reading, but the absence of a feature in public material is not proof it doesn't exist. Phrased as "not described in public material reviewed", never "does not have".
- **PROPOSED** — design intent for our prototype; not yet implemented.
- **EXPERIMENTALLY VALIDATED** — demonstrated by our own benchmark/tests with recorded numbers (reserved for later phases).
- **NOT YET VALIDATED** — a hypothesis about decision value that we must test (Phase 16+).

---

## Ledger

| # | Claim | Class | Evidence | Source | Notes / Status |
| --- | --- | --- | --- | --- | --- |
| 1 | IcySea (Drift+Noise, ESA InCubed) bundles near-real-time sea-ice information — SIC, high-res SAR imagery, ice-drift forecasts, automatic ice classification — into a low-bandwidth app for polar vessels | VERIFIED | ESA InCubed activity page; operator interview | Sources 1–3 in gap doc | Completed 2024 as InCubed activity; commercial field use |
| 2 | IcySea's automatic route optimisation for ships through ice is (at least partly) still in development as of late 2024 | VERIFIED | Operator statement in Oct 2024 interview | Source 2 | Interview: "another idea in development" |
| 3 | IcySea does not publicly describe probabilistic iceberg-trajectory prediction, multi-route trade-off comparison, or an explanation of route choice | INFERRED | Absence in reviewed ESA/operator/Copernicus material | Sources 1–3 | Must revisit if new material appears; phrase carefully |
| 4 | PolarRoute (BAS AI Lab; Smith et al. 2022) performs vessel-specific route optimisation over changing polar environmental fields using non-uniform meshes, mesh-optimal paths, smoothing, and data-driven vessel speed/fuel functions | VERIFIED | Peer-reviewed paper (arXiv:2209.02389) | Source 4 | Demonstrated for RRS *Sir David Attenborough*, Weddell Sea; Arctic/Baltic examples |
| 5 | PolarRoute routes respond to objective function, seasonal ice variability, and currents | VERIFIED | Paper abstract/text | Source 4 | Foundation for our sensitivity arguments |
| 6 | PolarRoute is research-stage (paper + internal BAS tooling), not a public decision-support product with route trade-off UI, explanation, or re-route alerting | VERIFIED (research-stage) + INFERRED (absence of product features) | Paper; BAS project page; BAS-linked article | Sources 4–6, 11 | Split class — the absence part stays INFERRED |
| 7 | BAS AI Lab plans to feed IceNet sea-ice forecasts into route planning and add ecological layers | VERIFIED | BAS-authored WWF *The Circle* article (2025) | Source 11 | Confirms BAS is moving toward richer decision inputs |
| 8 | IceNet forecasts pan-Arctic and pan-Antarctic sea-ice concentration daily, ~25 km, months ahead | VERIFIED | BAS-authored article; IceNet literature | Source 11 | Our sea-ice forecast must acknowledge IceNet exists; we benchmark against persistence + simple ML, not against IceNet |
| 9 | DESIDE (ESA Use Case, Destination Earth) delivers dynamic sea-ice charts, ship-class-specific risk assessments based on the IMO Polaris algorithm, and optimised routing solutions | VERIFIED | DestinE use-case page; Polar View announcement | Sources 7–8 | Providers: Polar View, EOX, Drift+Noise, DMI, FMI, NMI |
| 10 | DESIDE scope is Baltic/European-Arctic first, with Antarctic included only as "rest of the polar regions" in public text | VERIFIED (text) / INFERRED (emphasis) | DestinE page wording | Source 7 | Antarctic capability not demonstrated in core deliverables |
| 11 | DESIDE disseminates tactical products through the IcySea app and strategic products through Polar Dashboard / Polar TEP | VERIFIED | DestinE page | Source 7 | Shows IcySea is part of a larger ecosystem |
| 12 | DESIDE does not publicly describe probabilistic iceberg-trajectory products, multi-route alternatives with explained recommendation, or dynamic re-routing | INFERRED | Absence in reviewed DestinE/Polar View material | Sources 7–8 | Revisit at judging time; programme evolving fast |
| 13 | Polar View Antarctic (polarview.aq) delivers satellite-derived sea-ice **and iceberg** information to ships in the Southern Ocean | VERIFIED | Polar View Antarctic portal; BAS project page | Sources 9–10 | Observation/nowcast service, not forecast or routing |
| 14 | Academic Antarctic route-optimisation exists, including an Indian Bharati–Maitri case study using Dijkstra's algorithm over ice and wind resistance | VERIFIED | Mishra et al. 2021, Polar Science 30 | Source 12 | Our direct academic benchmark |
| 15 | A Web-GIS safer-navigation system for the Maitri–Bharati region exists (Indian national work) | VERIFIED | Gupta et al. 2019, ISG proceedings | Source 13 | Context for NCPOR relevance |
| 16 | Operational Antarctic iceberg products are presence-based and coarse (e.g., NAVAREA VI grid-cell iceberg counts from SAR), not probabilistic trajectory forecasts | VERIFIED | Arctic Institute 2026 review (Scardilli et al.), citing Salvó et al. 2023 | Source 15 | The baseline our iceberg hazard must beat |
| 17 | Antarctic sea-ice has entered a possible regime of record-low extents, making navigation hazards more dynamic | VERIFIED | Purich & Doddridge 2023 via Arctic Institute review | Source 15 | Motivates the problem; also cited in project-definition risk register |
| 18 | Antarctic maritime activity is growing (e.g., >120k Antarctic tourists in 2023–24 across 50+ vessels) | VERIFIED | IAATO report via Arctic Institute review | Source 15 | Stakeholder relevance for NCPOR/MoES |
| 19 | Our system converts probabilistic environmental forecasts (incl. iceberg trajectory probability) into a unified vessel-specific hazard field H(x,t,v) with hard/soft constraints | EXPERIMENTALLY VALIDATED | Phase 10 hazard field with 4 components (ice/berg/weather/ocean), Phase 18 API exposing the full chain, SC-1 through SC-8 all passing | Phase 10+18 gate logs + Phase 19 acceptance tests | Validated on real Dec 2019–Mar 2020 data; vessel-specific differentiation demonstrated on OW/PC7/PC1 |
| 20 | Our system generates competing route alternatives (Fastest / Safest / Balanced) with quantified safety/time/fuel trade-offs | EXPERIMENTALLY VALIDATED | Phase 12 recorded run data/routing/latest.json (PC1 day-45: 3 routes + metrics + shortest-path baseline on the same ledger) + Phase 13 data/tradeoff/latest.json (comparison tables, priority-profile recommendations, sensitivity matrix) | Phase 12+13 gate logs | Routes + comparison + recommendation validated; narrative explanation is Phase 14 |
| 21 | Our system explains its route recommendation in decision terms and recomputes it dynamically when conditions change | EXPERIMENTALLY VALIDATED | Phase 14 data/explanation/latest.json (template explanations, recorded) + Phase 15 data/rerouting/latest.json (control + SC-5 re-route notices with triggers and deltas) | Phase 14+15 gate logs | Validated on recorded offline scenarios; live-feed operation explicitly out of scope |
| 22 | No surveyed public system offers the full integrated chain (probabilistic inputs → vessel hazard → multi-route trade-offs → explained recommendation → dynamic re-routing) for Antarctic operations | INFERRED | Review of six system categories (gap doc §3) | Gap analysis | Bounded by public material; our honest "gap" claim |
| 23 | Our uncertainty-aware multi-route decision layer improves navigation decisions relative to baselines (shortest path, persistence, constant-drift, academic routes) | PARTIALLY VALIDATED | Validated sub-claims: PC1 routes beat shortest-path (Phase 12); seasonal beats persistence (Phase 6); 7/10 backtest (Phase 16). Documented gaps: iceberg-ML tied baseline on synthetic tracks (Phase 7); academic-route benchmark (Mishra 2021) not yet compared. Full claim status: partial wins on real data; integrated improvement claim has two honest gaps | Phase 12+6+16 gate logs + Phase 19 audit | Phase 19 position: partially validated with honest gaps; pitch adjusted per §38 no-fake-completion rule |
| 24 | Our prototype is a decision-support system, not an autonomous or certified navigation system | VERIFIED (by definition of our scope) | Project definition §constraints | Project definition | Repeated in every demo/defence; never claim operational certification |

---

## 2. Claim-use discipline (team rules)

1. **In presentations**, PROPOSED claims are stated in future/design language ("our system will…", "we target…"), and INFERRED claims about others in careful language ("no public material we reviewed describes…"). NEVER: "IcySea has no route optimisation" (it lists it; operator says it's in development). NEVER: "PolarRoute lacks uncertainty" as fact.
2. **Promotion ceremony:** a claim moves from PROPOSED → EXPERIMENTALLY VALIDATED only after a recorded benchmark in `docs/` with numbers (e.g., route trade-off metrics, forecast MAE vs. persistence). Update this ledger at each phase gate.
3. **Re-verification:** competitor claims (#1–18) are re-checked immediately before the final demo and at any point a judge-facing statement relies on them; sources are re-accessed and dates recorded.
4. **If a claim fails validation** (#23 especially): record it, do not delete it, and adjust the pitch accordingly (Phase 19 failure-analysis rule).

---

## 3. Positioning statement (derived from this ledger — Phase 1 wording)

> Existing systems provide ice information (IcySea, Polar View), vessel-aware route computation (PolarRoute), and decision-enhancement products (DESIDE, Arctic/Baltic-led). None of the public material we reviewed demonstrates the full **Antarctic decision layer**: probabilistic forecasts — including iceberg trajectory probability, which operational iceberg products lack — converted into a vessel-specific hazard field, presented as competing route alternatives with quantified trade-offs, an explained recommendation, and dynamic re-routing. Our prototype implements and benchmarks that layer; it is a decision-support system, not a replacement for human navigators, and it is validated against documented baselines before any improvement is claimed.

Sources: as listed in `docs/existing-solutions-gap.md` §7 (accessed 2026-09-04).
