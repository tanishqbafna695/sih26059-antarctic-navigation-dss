# Existing Solutions & Gap Analysis — SIH26059

**Phase:** 1
**Last updated:** 2026-09-04
**Method:** Web research of primary sources (ESA, BAS, Destination Earth, Polar View, project interviews, peer-reviewed literature). Every capability claim below carries a source and a **verification class**:
- **VERIFIED** — stated by the operator/owner in a primary source we read.
- **INFERRED** — reasonable reading of the sources, but the absence of a feature is not a confirmed fact (absence of evidence ≠ evidence of absence).
- **PROPOSED / NOT YET VALIDATED** — about *our own* planned system.

Rule applied throughout: we never write "System X lacks feature Y" without marking it INFERRED from public material, because non-public versions may differ.

---

## 1. Why this review matters

The SIH26059 problem is *not* new in its parts — sea-ice information services, polar route planners, and ship-routing research all exist. The gap we can defensibly occupy is **integration of the decision layer**. To claim that honestly, we must know precisely what the leading systems do and do not describe publicly. This document is the evidence base for the "Why not IcySea?" / "Why not PolarRoute?" defences and for every row of the innovation ledger (`docs/innovation-claims.md`).

---

## 2. System profiles (verified)

### 2.1 IcySea — Drift+Noise Polar Services GmbH (Germany)

| Attribute | Finding |
| --- | --- |
| What it is | Progressive web app bundling near-real-time (NRT) sea-ice data for polar maritime operations; low-bandwidth optimised (kilobyte/MB downloads for the user's area) |
| Funding / status | ESA InCubed product-development activity (completed 2024); commercial service in field use |
| Coverage | Arctic and Antarctic; SAR imagery extended to both regions; Arctic-wide sea-ice-drift forecast trajectories; Svalbard ML-optimised drift forecasts |
| Core data layers | Sea-ice concentration (6 km product originally, 3 km product integrated), high-resolution SAR imagery (Sentinel-1, RADARSAT Constellation Mission as fallback), ice-drift forecasts, automatic ice classification |
| Route features | ESA InCubed product page lists "automatic route optimisation" among main innovations and a "measurement tool for route planning" |
| Nuance (important) | In an October 2024 interview, Drift+Noise's research/field-support specialist states automatic *route suggestions* for ships through ice — based on ship and ice characteristics — are "another idea in development." We therefore treat **route optimisation as early-stage / partially in development**, not a mature multi-objective route product |
| What it is not (publicly) | Not a probabilistic forecast or uncertainty layer; no iceberg-trajectory prediction described; no multi-route (fastest/safest/balanced) trade-off comparison; no explanation of *why* one route is preferable; no dynamic re-route recommendation loop |

Sources: ESA InCubed activity page (incubed.esa.int/portfolio/esa-incubed-icysea/); Arctic Focus interview with Jakob Bünger, Drift+Noise (arcticfocus.org, 2024); Copernicus Marine use-case page.

### 2.2 BAS PolarRoute + Logist programme — British Antarctic Survey (BAS AI Lab)

| Attribute | Finding |
| --- | --- |
| What it is | Research-grade method and tooling for long-distance polar vessel route planning over changing sea-ice and ocean conditions |
| Method (peer-reviewed) | Smith et al. 2022 (arXiv:2209.02389, "Autonomous Passage Planning for a Polar Vessel"): three stages — discrete modelling of the environment on a **non-uniform mesh**; construction of **mesh-optimal paths**; **path smoothing**. Data-driven functions map each mesh cell to **vessel speed limits and fuel requirements** |
| Vessel-specificity | YES — VERIFIED. Functions account for different vehicle properties; demonstrated for RRS *Sir David Attenborough* (ice-performance characteristics) |
| Demonstration region | Weddell Sea, Antarctica; additional examples in the Arctic Ocean and Baltic Sea |
| Sensitivity demonstrated | Routes change with seasonal sea-ice variability, choice of objective function, and presence of currents |
| Programme umbrella | BAS project "Logist — AI for environmentally aware decision support": described as "an AI route planner that acts like a Google Maps for the polar oceans... plan the optimal route between a set of points for a given vessel" |
| Ecosystem | BAS AI Lab uses IceNet sea-ice forecasts (pan-Arctic *and* pan-Antarctic, 25 km, daily, months ahead) as inputs and is adding ecological layers (wildlife presence) to route planning |
| What it is not (publicly) | A public, human-in-the-loop **decision-support product**: no described UI presenting competing route alternatives with an explicit safety/time/fuel trade-off table; no explanation engine justifying a recommendation; no described probabilistic iceberg-trajectory hazard; no described operator alert-and-re-route loop. The paper optimises *an* optimal path per objective function rather than presenting a decision set with quantified trade-offs |

Sources: arXiv:2209.02389; BAS project page "Logist AI for environmentally aware decision support" (bas.ac.uk); WWF Arctic "The Circle" 2025 article by B. N. Ubald & J. Smith (BAS); Zenodo poster "PolarRoute: Optimal maritime routing for the RRS Sir David Attenborough" (2026).

### 2.3 DESIDE — DestinE Sea Ice Decision Enhancement (EU Destination Earth, ESA Use Case)

| Attribute | Finding |
| --- | --- |
| What it is | ESA Use Case under the EU Destination Earth (DestinE) programme; delivers decision-enhancement products for polar and Baltic operations |
| Providers | Polar View (lead), EOX IT Services, Drift+Noise, Danish Meteorological Institute, Finnish Meteorological Institute, Norwegian Meteorological Institute |
| Geographic scope | Baltic Sea and European Arctic Ocean first, plus "the rest of the polar regions" (Antarctic coverage therefore secondary/aspirational in public text, not the demonstrated core) |
| Products | Multi-tier: **Execution support** (short-term, days — tactical), **planning support** (mid-term, weeks — voyage planning), **strategy/policy support** (long-term, seasons — climate scenarios). Specific deliverables: dynamic sea-ice charts, **ship-class-specific risk assessments based on the IMO Polaris algorithm**, and **optimised routing solutions** to cut fuel/emissions |
| Dissemination | IcySea app as the near-real-time execution front end; Polar Dashboard and Polar TEP for longer-range planning/analytics |
| What it is not (publicly) | Not described as Antarctic-first; risk assessment is **ship-class** (Polaris/IMO risk-index logic), not full vessel-specific multi-objective routing; no iceberg-trajectory product described; no described UI comparing multiple route alternatives with an explanation of the recommendation |

Sources: destination-earth.eu/use-cases/deside/; polarview.org news announcement; ECMWF DestinE pages.

### 2.4 Polar View (Antarctic service, polarview.aq)

| Attribute | Finding |
| --- | --- |
| What it is | Operational near-real-time sea-ice **information service** for the Southern Ocean; consortium-based (BAS involvement historically); a polarview.aq web portal plus OGC (WFS/GeoServer) data feeds |
| Coverage of interest | Delivers satellite-derived **sea-ice and iceberg information directly to ships** in the Southern Ocean |
| Nature | Observation/nowcast information delivery (ice charts, imagery) — free at point of use historically; not an ML forecast or route-optimisation platform; sister org Polar View EO Ltd now coordinates DESIDE |

Sources: polarview.aq; BAS Polar View project page; Polar View data-platforms page.

### 2.5 DESIDE-adjacent EU programmes (noted, not competitors to analyse deeply)

- **Copernicus Marine Service / OSI SAF** — authoritative sea-ice data feeds we will *use* as input.
- **Polar TEP** — ESA Thematic Exploitation Platform for polar data processing/visualisation (a data platform, not a route recommender).
- **AutoICE** — ML sea-ice-charting research challenge (Polar View); relevant to automated ice classification that systems like IcySea feed on.

### 2.6 Academic & national research (incl. NCPOR-relevant work)

| Work | Finding |
| --- | --- |
| Mishra et al. 2021, *Polar Science* 30 | "Investigating optimum ship route in the Antarctic in presence of sea ice and wind resistances – a case study between **Bharati and Maitri**." Dijkstra-based shortest-path optimisation over ice/wind resistance between the two Indian Antarctic stations. **Directly NCPOR-relevant academic baseline** |
| Gupta et al. 2019 (ISG) | Web-GIS-based system for safer ship navigation near Maitri (70°45′ S, 11°43′ E) and Bharati (69°24′ S, 76°11′ E), combining satellite data and sea-ice/wind resistance — Indian national context |
| NRC Canada (2023) | "Pathfinding and optimization for vessels in ice: a literature review" — third-party survey confirming a large, active academic field (A*, Dijkstra, dynamic programming, optimal control, graph methods) |
| Hou et al. 2025, *Environ. Res. Lett.* | Future Antarctic marine accessibility under warming — long-horizon accessibility research citing the Bharati–Maitri case study |

**Consequence for us:** a Dijkstra/A*-over-cost-field routing core is *standard*, and an Indian Bharati–Maitri route study already exists. Our route *computation* will not be novel; our **decision presentation** (alternatives + trade-offs + explanation + re-routing) is where we add value. Academic baselines give us exact benchmarks to compare against (Phase 16).

Sources: ScienceDirect S1873965221000736 listing; NRC Publications record; ISG India proceedings PDF.

### 2.7 Iceberg-monitoring reality (context for the hazard problem)

- Antarctic iceberg monitoring relies on **SAR satellite imagery**; in-situ observations are scarce (Salvó et al. 2023; Arctic Institute 2026 review).
- Operational products (NAVAREA/METAREA bulletins, ice services) report iceberg *presence* — e.g., Argentina's NAVAREA VI analysis classifies 1°×1° grid cells by iceberg count (isolated/few/many) — i.e., **coarse, presence-based risk, not probabilistic trajectory prediction**.
- A possible Antarctic sea-ice **regime shift** toward record-low winter extents (Purich & Doddridge 2023) makes navigation hazards more dynamic; Antarctic tourism alone exceeded 120,000 visitors in 2023–24 (IAATO via Arctic Institute).

**Consequence for us:** a probabilistic *iceberg-trajectory* hazard fed into routing is not something the surveyed operational systems provide, and operational iceberg products are much coarser than what our decision layer will represent. This is a genuine (if research-grade) gap — to be demonstrated, not merely asserted.

---

## 3. Comparison matrix

Legend: ● = described in primary sources as offered/doing this; ◐ = partial / early-stage / secondary scope; ○ = not described in public material we reviewed (INFERRED); — = not applicable / unclear.

| Capability | IcySea | PolarRoute (BAS) | DESIDE (DestinE) | Polar View (Antarctic) | Academic (e.g., Bharati–Maitri) | **Our System (target)** |
| --- | --- | --- | --- | --- | --- | --- |
| Sea-ice observation / nowcast delivery | ● | ◐ (input) | ● | ● | — | ● (input) |
| Sea-ice *forecast* (ML or otherwise) | ◐ (drift forecasts) | ● (via IceNet inputs) | ● | ○ | — | ● (ML forecast + baseline) |
| Probabilistic/uncertainty representation | ○ | ○ (not described) | ◐ (not core product) | ○ | ○ | ● (core) |
| Iceberg trajectory prediction (probabilistic) | ○ | ○ | ○ | ◐ (presence info only) | ○ | ● (core) |
| Vessel-specific route optimisation | ◐ (in development) | ● (paper-proven) | ◐ (ship-class risk, routing) | ○ | ◐ (station-pair case studies) | ● |
| Multiple route alternatives (Fastest/Safest/Balanced) | ○ | ◐ (different objective functions, single route each) | ○ (not described) | ○ | ○ | ● (core) |
| Explicit safety/time/fuel trade-off comparison | ○ | ◐ (objectives in research) | ◐ | ○ | ○ | ● (core) |
| Explainable recommendation ("why this route") | ○ | ○ | ○ | ○ | ○ | ● (core) |
| Dynamic re-routing on environmental change | ○ | ◐ (research capacity) | ○ (not described) | ○ | ○ | ● (core) |
| Human-in-the-loop decision framing | ◐ (captain interprets data) | ◐ (captain-in-loop described in paper) | ◐ | ◐ | ○ | ● (explicit) |
| Data quality / provenance tracking | ◐ | ◐ | ◐ | ◐ | — | ● (goal) |
| Antarctic-first focus | ● | ● (Weddell demo) | ◐ (Arctic/Baltic first) | ● | ● (Indian stations) | ● |

Notes on the most contestable cells:
- **PolarRoute "single route per objective"** — VERIFIED from paper methodology (optimised paths per objective function; route sensitivity demonstrated). "No trade-off decision UI" is INFERRED from public material.
- **DESIDE Antarctic coverage** — VERIFIED as text ("rest of the polar regions"); its Arctic/Baltic-first emphasis is our reading of the same text.
- **IcySea route optimisation** — VERIFIED as contested/early: ESA lists it as an innovation; the operator's 2024 interview describes auto-route as an idea in development.
- **Iceberg rows for everyone except Polar View** — INFERRED from absence in reviewed sources. We must be ready to update if new material appears.

---

## 4. The defensible gap

Across the six categories above, three things are each partially covered by somebody, but **no surveyed system publicly describes the full chain** for Antarctic operations:

1. **Uncertainty-aware probabilistic inputs** (sea-ice concentration ± uncertainty; iceberg position probability), rather than deterministic fields or presence-based warnings;
2. **A unified vessel-specific hazard field** combining sea ice, iceberg probability, weather/ocean state, and vessel capability with hard vs. soft constraint logic;
3. **A visible decision layer** on top of routing: competing route alternatives, quantified safety/time/fuel trade-offs, an *explained* recommendation, and **dynamic re-routing when conditions change** — framed for a human navigator.

Existing systems each cover a slice: IcySea = best-in-class ice *information delivery*; PolarRoute = rigorous vessel-aware route *computation*; DESIDE = broad DestinE-based *decision-enhancement programme* (Arctic/Baltic-led); Polar View = operational ice/iceberg *information*; academic work = route-optimisation *methods* and NCPOR-relevant case studies.

Our contribution, phrased for judges:

> Existing systems provide ice information (IcySea, Polar View), vessel-aware route computation (PolarRoute), and decision-enhancement products (DESIDE). Our prototype focuses on the **decision layer**: it converts probabilistic Antarctic forecasts — including iceberg trajectory probability, which operational products do not provide — into a vessel-specific hazard field, generates competing route alternatives, quantifies the safety/time/fuel trade-offs, explains its recommendation, and recomputes the decision when conditions change. We benchmark our forecasts against persistence and constant-drift baselines and our routes against shortest-path and academic baselines (e.g., Bharati–Maitri studies) to demonstrate measurable decision value.

We make **no claim** that no other system can or will do this; we claim only that this *integrated, uncertainty-aware decision layer* is the focus of our prototype and is not publicly demonstrated as a coherent product by the systems we reviewed.

---

## 5. Canned defences (evidence-backed)

### "Why not IcySea?"
IcySea is an excellent near-real-time ice-information service (SAR imagery, concentration, drift forecasts, ice classification) used operationally on polar vessels. It is not described — including by its own operator — as providing probabilistic iceberg trajectories, a multi-route decision set with quantified trade-offs, or an explained, dynamically updated route recommendation; its automatic route optimisation was still described as in development in 2024. Our system *uses* the same class of data as input and adds the decision layer on top; we are complementary, not a replacement.

### "Why not PolarRoute?"
PolarRoute (BAS) is the closest benchmark: peer-reviewed, vessel-specific, environment-aware route construction demonstrated for RRS *Sir David Attenborough* in the Weddell Sea, with routes that respond to objective function, seasonality, and currents. Our focus is different: PolarRoute computes an optimised path; our prototype presents **competing route alternatives with explicit trade-offs**, an explanation of the recommendation, uncertainty representation, probabilistic iceberg hazard, and a human-in-the-loop re-routing loop — the decision *presentation and update* layer around a route computation core we acknowledge and build upon.

### "Why not DESIDE?"
DESIDE is an ambitious DestinE use case producing dynamic ice charts, Polaris-based ship-class risk, and routing for Baltic/European-Arctic-first scope, disseminated via IcySea, Polar Dashboard, and Polar TEP. It validates the direction we propose. Our prototype is Antarctic-first, smaller-scale, and student-built; our demonstrable differentiators are probabilistic iceberg trajectory hazard, multi-route trade-off presentation with explanation, and dynamic re-routing — features not described among DESIDE's core deliverables.

---

## 6. Implications for our architecture (decisions locked for later phases)

1. **Route core:** adopt graph-based optimisation (A*/Dijkstra over a cost field) as the *baseline* method — matching academic practice — then layer multi-objective costs (risk, time, fuel) on top. Do not over-engineer the search algorithm; the decision layer is the differentiator. (Phases 10–13)
2. **Data plan:** rely on Copernicus/OSI-SAF-class sea-ice concentration and drift, ERA5-class weather, and SAR-derived iceberg observations where available — the same feeds the operational systems use — so our contribution stays at the decision layer, not data invention. (Phase 3–4)
3. **Iceberg hazard:** operational practice (NAVAREA grids, presence counts) is the baseline to beat with trajectory probability. (Phases 7, 10)
4. **NCPOR relevance:** Bharati–Maitri (and Bharati/coastal ↔ ice-edge transits) are the natural demo scenarios, benchmarking against Mishra et al. 2021 and Gupta et al. 2019 where data allow. (Phases 12–20)
5. **Positioning:** we are an *Antarctic-first decision-support prototype* that integrates existing data classes and acknowledged route methods into an uncertainty-aware, explainable, re-routable decision loop. (All phases)

---

## 7. Sources

Accessed 2026-09-04.
1. ESA InCubed — *IcySea* activity page. https://incubed.esa.int/portfolio/esa-incubed-icysea/
2. Arctic Focus (2024) — *Navigating the Frozen Frontier: How IcySea Revolutionizes Polar Ice Navigation* (interview with J. Bünger, Drift+Noise). https://www.arcticfocus.org/stories/navigating-frozen-frontier-how-icysea-revolutionizes-polar-ice-navigation/
3. Copernicus Marine Service — *IcySea: a new ice information app for navigation in polar regions*. https://marine.copernicus.eu/services/use-cases/icysea-new-ice-information-app-navigation-polar-regions
4. Smith, J.D. et al. (2022) — *Autonomous Passage Planning for a Polar Vessel*. arXiv:2209.02389. https://arxiv.org/abs/2209.02389
5. BAS — *Logist: AI for environmentally aware decision support* (project page). https://www.bas.ac.uk/project/logist-ai-for-environmentally-aware-decision-support/
6. Zenodo (2026) — *PolarRoute: Optimal maritime routing for the RRS Sir David Attenborough* (poster record). https://zenodo.org/records/22129790
7. Destination Earth — *DESIDE* use-case page. https://destination-earth.eu/use-cases/deside/
8. Polar View — *DestinE DESP Use Cases: DESIDE* announcement. https://polarview.org/news-press/destination-earth-desp-use-cases-destine-sea-ice-decision-enhancement-deside/
9. Polar View Antarctic portal. https://www.polarview.aq/ and https://www.polarview.aq/antarctic
10. BAS — *Polar View* project page. https://www.bas.ac.uk/project/polarview/
11. WWF Arctic, *The Circle* 2025.03 — Ubald, B.N. & Smith, J., *Navigating a changing ice world*. https://www.arcticwwf.org/the-circle/stories/navigating-a-changing-ice-world/
12. Mishra, P. et al. (2021) — *Investigating optimum ship route in the Antarctic in presence of sea ice and wind resistances – a case study between Bharati and Maitri*. Polar Science 30. ScienceDirect S1873965221000736.
13. Gupta, U.K. et al. (2019) — *Development of a Web-GIS based system for safer ship navigation* (ISG India proceedings). isgindia.org PDF.
14. NRC Canada (2023) — *Pathfinding and optimization for vessels in ice: a literature review*. nrc-publications.canada.ca (b323558e-…).
15. The Arctic Institute (2026) — *Icebergs and Navigation Safety in Antarctica* (Scardilli, Tiranti, Jaimes), incl. Salvó et al. 2023 (Front. Mar. Sci.) and Purich & Doddridge 2023 (*Commun. Earth Environ.*) citations. https://www.thearcticinstitute.org/icebergs-navigation-safety-antarctica-possible-impact-new-sea-ice-regime-southern-ocean-south-atlantic-ocean/
16. Hou, Y. et al. (2025) — *Future Antarctic marine accessibility in a warming world*. Environ. Res. Lett. (IOP).
