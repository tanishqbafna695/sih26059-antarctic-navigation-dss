# Judge Defence — SIH26059

**Problem:** AI-Enabled Antarctic Sea-Ice, Iceberg Trajectory, and Navigation Decision Support System
**Team:** Freebuff | **Organization:** MoES / NCPOR

---

## 1. The Pitch (60 seconds)

**Prediction is not the final problem. Decision-making under uncertainty is.**

Existing systems provide ice information (IcySea, Polar View) and vessel-aware route computation (PolarRoute). None of the public material we reviewed demonstrates the full **Antarctic decision layer**: probabilistic forecasts — including iceberg trajectory probability, which operational iceberg products lack — converted into a vessel-specific hazard field, presented as competing route alternatives with quantified trade-offs, an explained recommendation, and dynamic re-routing.

Our prototype implements that layer. It is a decision-support system, not a replacement for human navigators. Every claim is backed by recorded numbers on real satellite data.

---

## 2. What We Built (evidence in 60 seconds)

| Capability | Phase | Evidence |
|---|---|---|
| Sea-ice forecast beats persistence | Phase 6 | Seasonal climatology RMSE 0.0487 vs persistence 0.0501 at h=5 on real Dec 2019–Mar 2020 data |
| Iceberg trajectory with uncertainty ellipses | Phase 7 | Physics model: 2.05 km @24h → 5.86 km @72h with growing uncertainty radius |
| Vessel-specific hazard field H(x,t,v) | Phase 10 | 35% ice + 35% iceberg + 20% weather + 10% ocean; hard/soft constraints per vessel class |
| Three route alternatives with trade-offs | Phase 12 | Fastest/Safest/Balanced with time, fuel, risk, ice exposure on the same ledger |
| Explained recommendation | Phase 14 | Template explanations with significance guards; "why this route" + "the price" |
| Dynamic re-routing | Phase 15 | RE-ROUTE/ADJUSTED/HOLDS with change detection and old-vs-new comparison |
| REST API (fully offline) | Phase 18 | 7 endpoints; full chain in 2.95s (NFR-3 limit: 120s) |
| Live demo UI | Phase 17/20 | React + MapLibre; vessel/priority select; provenance tooltips on every number |
| Acceptance tests SC-1 through SC-8 | Phase 19 | All 8 scenarios pass; 25/25 FRs validated; 145/145 tests green |

---

## 3. "Why Not IcySea?"

**What IcySea does well:** Near-real-time sea-ice information (SIC, SAR imagery, drift forecasts) delivered through a low-bandwidth progressive web app. ESA InCubed product, commercial field use since 2024.

**What we add that IcySea does not demonstrate publicly:**

| Our capability | IcySea public material | Source |
|---|---|---|
| Probabilistic iceberg trajectory prediction | Not described (presence-based only) | ESA InCubed page, operator interview (Oct 2024) |
| Multi-route trade-off comparison (Fastest/Safest/Balanced) | "Route optimisation" listed but in development per operator | Operator interview: "another idea in development" |
| Explained recommendation with quantified reasoning | Not described | Gap analysis §2.1 |
| Dynamic re-routing with old-vs-new comparison | Not described | Gap analysis §2.1 |

**Honest caveat:** IcySea is evolving fast. Our gap claims are bounded by public material reviewed as of 2026-09-04. Non-public versions may differ.

---

## 4. "Why Not PolarRoute?"

**What PolarRoute does well:** Vessel-specific route optimization over changing polar environmental fields using non-uniform meshes, mesh-optimal paths, and data-driven vessel speed/fuel functions. Peer-reviewed (Smith et al. 2022, arXiv:2209.02389).

**What we add that PolarRoute does not demonstrate publicly:**

| Our capability | PolarRoute public material | Source |
|---|---|---|
| Multi-route alternatives with trade-off comparison | Single optimal route per objective function | Paper (arXiv:2209.02389) |
| Explained recommendation in decision terms | Not described | Paper + BAS project page |
| Dynamic re-routing with change notification | Research tool; no alerting described | BAS project page, BAS-authored article |
| Probabilistic iceberg trajectory prediction | Not described (icebergs not in scope) | Paper scope: vessel routing, not iceberg hazard |

**Honest caveat:** PolarRoute is a research-grade tool from the British Antarctic Survey, not a public product. It may have capabilities beyond what public material describes.

---

## 5. "Why Not DESIDE?"

**What DESIDE does well:** Dynamic sea-ice charts, ship-class-specific risk assessments (IMO Polaris algorithm), optimised routing. ESA Use Case for Destination Earth.

**What we add that DESIDE does not demonstrate publicly:**

| Our capability | DESIDE public material | Source |
|---|---|---|
| Antarctic-focused (Bharati-Maitri corridor) | Baltic/European-Arctic first; Antarctic as "rest of polar regions" | DestinE use-case page |
| Probabilistic iceberg trajectory prediction | Not described | DestinE + Polar View pages |
| Multi-route alternatives with explained recommendation | Not described | Gap analysis §2.3 |
| Dynamic re-routing with old-vs-new comparison | Not described | Gap analysis §2.3 |

**Honest caveat:** DESIDE is a large consortium (Polar View, EOX, Drift+Noise, DMI, FMI, NMI) with evolving scope. Antarctic capability may expand.

---

## 6. Innovation Claims Summary

| # | Claim | Status | Evidence |
|---|---|---|---|
| 19 | Unified vessel-specific hazard field H(x,t,v) | ✅ EXPERIMENTALLY VALIDATED | Phase 10 + 18 (API) + SC-1 through SC-8 |
| 20 | Competing route alternatives with quantified trade-offs | ✅ EXPERIMENTALLY VALIDATED | Phase 12 + 13 recorded runs |
| 21 | Explained recommendation + dynamic re-routing | ✅ EXPERIMENTALLY VALIDATED | Phase 14 + 15 recorded runs |
| 22 | No surveyed system offers the full integrated chain | ⚠️ INFERRED | Gap analysis bounded by public material |
| 23 | Decision layer improves on baselines | ⚠️ PARTIALLY VALIDATED | Routing > shortest-path ✅; Forecast > persistence ✅; Iceberg ML = baseline (tied); Academic benchmark (pending) |
| 24 | Decision-support prototype, not certified navigation | ✅ VERIFIED | By definition of our scope |

**Claim #23 honest assessment:** We have demonstrated individual component improvements on real data. The integrated improvement claim has two documented gaps: (1) iceberg-ML ties the constant-velocity baseline on synthetic tracks, and (2) the academic-route benchmark (Mishra et al. 2021) has not been compared. We record these honestly rather than fabricating positive results.

---

## 7. Key Numbers for Judges

| Metric | Value | Context |
|---|---|---|
| Test suite | 145/145 green | 15 test modules, including 20 acceptance tests |
| Demo timing | 2.95s | Full SC-1 story; NFR-3 limit: 120s |
| Seasonal forecast vs persistence | RMSE 0.0487 vs 0.0501 | h=5, real held-out 2019-20 season |
| PC1 routes vs shortest-path | 221.2h / risk 0.038 vs 240.2h / risk 0.064 | Faster AND safer than baseline |
| Open Water RV | No route (FR-24) | Same environment, different vessel → different answer |
| Re-route trigger | Iceberg danger jump 0.999 | SC-5: new fix appears, system recomputes |
| Data | Real satellite data | OSI SAF SIC CDR + ERA5 (Dec 2019–Mar 2020) |
| Cost | Zero | All datasets free/open; all software open-source |

---

## 8. What We Do NOT Claim

- ❌ We do NOT claim to have invented polar route optimization (Dijkstra is standard).
- ❌ We do NOT claim operational certification or guaranteed safety.
- ❌ We do NOT claim our iceberg-ML outperforms constant-velocity on real tracks (it ties on synthetic; real tracks not yet downloaded).
- ❌ We do NOT claim the integrated decision layer is fully validated (claim #23 is partially validated with honest gaps).
- ❌ We do NOT claim our system replaces human navigators.

---

## 9. Honest Limitations

1. **GLORYS12 gap:** Ocean currents use wind-driven fallback. Confidence is DEGRADED.
2. **Single season:** Trained on Dec 2019–Mar 2020. Multi-season training available but not deployed to UI.
3. **Iceberg tracks:** Demo uses labeled ASSUMED fixes. Real BYU/NIC tracks need manual download.
4. **Corridor fixed:** Bharati→Maitri only. Free endpoints via API, not yet in UI.
5. **Academic benchmark:** Mishra et al. 2021 comparison pending.

---

## 10. Demo Checklist (for judges)

- [ ] API starts and responds at /docs (Swagger UI)
- [ ] UI loads with real sea-ice map
- [ ] Three routes visible with different colors
- [ ] Vessel switch (PC7 → PC1 → OW) changes results
- [ ] Priority switch moves the winner star
- [ ] "Why this advice" tab shows explanation
- [ ] "Data status" tab shows confidence + sources
- [ ] Update B shows re-route alarm
- [ ] Every number has a hover tooltip (NFR-4)
- [ ] Provenance traces to real satellite data
