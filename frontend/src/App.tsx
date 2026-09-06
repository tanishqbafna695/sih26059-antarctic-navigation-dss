import { useState } from "react";
import MapView, { type RouteLine } from "./components/MapView";
import SidePanel, { type PanelTab } from "./components/SidePanel";
import { PRIORITY_PROFILES, recommend } from "./lib/scoring";
import type { ComparisonRow } from "./lib/types";
import tradeoffBundle from "./data/tradeoff.json";
import explanationsBundle from "./data/explanations.json";
import routesBundle from "./data/routes.json";
import noticesBundle from "./data/notices.json";
import statusBundle from "./data/status.json";
import corridor from "./data/corridor.json";
import bergsBundle from "./data/bergs.json";
import vesselsBundle from "./data/vessels.json";
import ice45 from "./data/ice_45.png";
import ice50 from "./data/ice_50.png";
import hazard45 from "./data/hazard_45_pc7.png";

type VesselId = "polar_class_pc7" | "polar_class_pc1" | "open_water_rv";
type Scenario = "plan" | "A" | "B";

const COLORS: Record<string, string> = {
  fastest: "#ff9d66",
  safest: "#5ce08a",
  balanced: "#6fb7ff",
};
const ICE: Record<string, string> = { plan: ice45, A: ice50, B: ice50 };

interface CompRow {
  route: string; travel_time_h: number; fuel_liters: number;
  mean_hazard: number; max_hazard: number; ice_exposure_frac: number;
  mean_iceberg_hazard: number;
}

export default function App() {
  const [vessel, setVessel] = useState<VesselId>("polar_class_pc7");
  const [scenario, setScenario] = useState<Scenario>("plan");
  const [profile, setProfile] = useState("balanced");
  const [tab, setTab] = useState<PanelTab>("routes");
  const [showIce, setShowIce] = useState(true);
  const [showHazard, setShowHazard] = useState(false);
  const [showBergs, setShowBergs] = useState(true);
  const [showRoutes, setShowRoutes] = useState<Record<string, boolean>>({
    fastest: true, safest: true, balanced: true });

  const effScenario: Scenario = vessel === "polar_class_pc7" ? scenario : "plan";
  const tradeoff = tradeoffBundle as unknown as Record<string, {
    comparison: { routes_available: boolean; reason?: string; rows: CompRow[];
      confidence: { overall_confidence: number; status_label: string } };
    recommendations: Record<string, { recommended: string }>;
  }>;
  const comp = tradeoff[vessel].comparison;

  // ---- plan-mode live recommendation ----
  let rows: ComparisonRow[] = [];
  let winner: string | null = null;
  let parityNote: string | null = null;
  let noRouteReason: string | null = null;
  if (!comp.routes_available) {
    noRouteReason = comp.reason ?? "no acceptable route";
  } else {
    rows = comp.rows
      .filter((r) => ["fastest", "safest", "balanced"].includes(r.route))
      .map((r) => ({ route: r.route, time_h: r.travel_time_h,
        fuel_l: r.fuel_liters, risk: r.mean_hazard,
        ice_exp: r.ice_exposure_frac * 100, berg: r.mean_iceberg_hazard }));
    const rec = recommend(rows, profile);
    winner = rec.winner;
    const recorded = tradeoff[vessel].recommendations[profile]?.recommended;
    parityNote = `Live recomputation under “${profile}” ${rec.winner === recorded ? "matches" : "DIFFERS FROM"} the recorded engine output (${recorded}).`;
  }

  // ---- map lines ----
  const routes = routesBundle as unknown as {
    plan45: Record<string, Record<string, { coords: number[][] }>>;
    rerouteA: RerouteEntry; rerouteB: RerouteEntry;
  };
  interface RerouteEntry {
    outcome: string; trigger: string; winner?: string;
    old_remaining?: number[][]; new?: Record<string, { coords: number[][] }>;
  }
  let lines: RouteLine[] = [];
  let oldLine: number[][] | null = null;
  if (effScenario === "plan" && !noRouteReason) {
    const pr = routes.plan45[vessel];
    lines = ["fastest", "safest", "balanced"].map((n) => ({
      id: n, coords: pr[n].coords, color: COLORS[n],
      width: n === winner ? 4 : 2.5, dashed: n !== winner,
      visible: showRoutes[n] ?? true }));
  } else if (effScenario !== "plan") {
    const entry = effScenario === "A" ? routes.rerouteA : routes.rerouteB;
    if (entry.old_remaining) oldLine = entry.old_remaining;
    if (entry.new && entry.winner && entry.new[entry.winner])
      lines = [{ id: "new", coords: entry.new[entry.winner].coords,
        color: "#5ce08a", width: 4, dashed: false, visible: true }];
  }

  // ---- bergs (hide the day-50 injection except in scenario B) ----
  const bergList = bergsBundle as unknown as
    { lon: number; lat: number; label: string; buffer_poly: number[][][] }[];
  const bergsShown = bergList.filter((b) =>
    effScenario === "B" ? true : !b.label.includes("SC-5"));
  const bergs = {
    buffers: { type: "FeatureCollection" as const, features: bergsShown.map((b) => ({
      type: "Feature" as const, properties: {},
      geometry: { type: "Polygon" as const, coordinates: b.buffer_poly } })) },
    fixes: { type: "FeatureCollection" as const, features: bergsShown.map((b) => ({
      type: "Feature" as const, properties: {},
      geometry: { type: "Point" as const, coordinates: [b.lon, b.lat] } })) },
  };

  // ---- side panel content ----
  const notices = noticesBundle as unknown as Record<string,
    { outcome: string; trigger: string; change_text: string; new_headline: string }>;
  const explanations = explanationsBundle as unknown as Record<string, {
    explained: boolean; headline?: string; strengths?: string[];
    prices?: string[]; vessel_statement?: string; confidence_note?: string;
    caveats?: string[]; reason?: string;
  }>;
  const tableRows = effScenario === "plan"
    ? rows.map((r) => ({ route: r.route, time_h: r.time_h, fuel_l: r.fuel_l,
        risk: r.risk, ice_exp_pct: r.ice_exp }))
    : [];
  const why = effScenario === "plan" && !noRouteReason
    ? (() => { const e = explanations[vessel];
        return e.explained ? { headline: e.headline ?? "", strengths: e.strengths ?? [],
          prices: e.prices ?? [], vessel_statement: e.vessel_statement ?? "",
          confidence_note: e.confidence_note ?? "", caveats: e.caveats ?? [] } : null; })()
    : null;
  const whyNote = effScenario === "plan" && profile !== "balanced"
    ? "Written reasons reflect balanced priorities; the ★ above follows your selected profile."
    : null;
  const notice = effScenario === "plan" ? null : (() => {
    const n = notices[effScenario === "A" ? "rerouteA" : "rerouteB"];
    return { outcome: n.outcome, trigger: n.trigger, change_text: n.change_text };
  })();

  const status = statusBundle as unknown as {
    depart_date: string;
    confidence: { overall_confidence: number; status_label: string };
    ocean_source: string; sources: string[]; honesty: string;
  };
  const statusLines = [
    `Sailing window opens ${status.depart_date}; ice: real OSI SAF record.`,
    `Route-set confidence ${(status.confidence.overall_confidence * 100).toFixed(0)}% (${status.confidence.status_label}) — shared across options.`,
    `Ocean currents: ${status.ocean_source}.`,
    ...status.sources.map((s) => `Source: ${s}.`),
    status.honesty,
    effScenario !== "plan"
      ? `Re-route view: grey dashes = previous course, green = new advice (${notice?.outcome}).`
      : "Corridor is fixed in this demo; free origin/destination arrives with the Phase 18 API.",
  ];

  const vessels = vesselsBundle as unknown as Record<string, { name: string; class: string }>;

  return (
    <div>
      <header>
        <h1>🧊 Antarctic ship-route advisor — demo</h1>
        <div className="sub">
          Satellite ice in, three explained route options out. A human navigator always decides.
          Corridor: {corridor.from.name} → {corridor.to.name}. All numbers computed by the system.
        </div>
      </header>
      <div className="controls">
        <label>Vessel
          <select value={vessel} onChange={(e) => setVessel(e.target.value as VesselId)}>
            {(Object.keys(vessels) as VesselId[]).map((v) => (
              <option key={v} value={v}>{vessels[v].name}</option>))}
          </select>
        </label>
        <label>View
          <select value={scenario} onChange={(e) => setScenario(e.target.value as Scenario)}>
            <option value="plan">Plan: 3 routes</option>
            <option value="A" disabled={vessel !== "polar_class_pc7"}>
              Update A: new observations{ vessel !== "polar_class_pc7" ? " (PC7 only)" : ""}</option>
            <option value="B" disabled={vessel !== "polar_class_pc7"}>
              Update B: iceberg alarm (ASSUMED){ vessel !== "polar_class_pc7" ? " (PC7 only)" : ""}</option>
          </select>
        </label>
        <label>Priorities
          <select value={profile} onChange={(e) => setProfile(e.target.value)}
            disabled={effScenario !== "plan"}>
            {Object.keys(PRIORITY_PROFILES).map((p) => (
              <option key={p} value={p}>{p.replace("_", " ")}</option>))}
          </select>
        </label>
        <label className="chk"><input type="checkbox" checked={showIce}
          onChange={(e) => setShowIce(e.target.checked)} /> ice</label>
        {effScenario === "plan" && vessel === "polar_class_pc7" && (
          <label className="chk"><input type="checkbox" checked={showHazard}
            onChange={(e) => setShowHazard(e.target.checked)} /> hazard field</label>)}
        <label className="chk"><input type="checkbox" checked={showBergs}
          onChange={(e) => setShowBergs(e.target.checked)} /> icebergs</label>
        {effScenario === "plan" && !noRouteReason && ["fastest", "safest", "balanced"].map((n) => (
          <label className="chk" key={n}>
            <input type="checkbox" checked={showRoutes[n] ?? true}
              onChange={(e) => setShowRoutes({ ...showRoutes, [n]: e.target.checked })} />
            <span className="dot" style={{ background: COLORS[n] }} /> {n}
          </label>))}
      </div>
      <main>
        <div className="card">
          <MapView iceUrl={ICE[effScenario]} showIce={showIce}
            hazardUrl={effScenario === "plan" && vessel === "polar_class_pc7" ? hazard45 : null}
            showHazard={showHazard} lines={lines} oldLine={oldLine}
            bergs={bergs} showBergs={showBergs} bbox={corridor.bbox as [[number, number], [number, number]]} />
          <div className="note">White = solid ice, blue = open water, grey = no satellite data.
            🟡 Bharati · 🔴 Maitri{effScenario !== "plan" ? " · grey dashes = previous course, green = new advice." : ""}</div>
        </div>
        <SidePanel tab={tab} setTab={setTab} rows={tableRows}
          winner={effScenario === "plan" ? winner : null} parityNote={effScenario === "plan" ? parityNote : null}
          noRouteReason={noRouteReason} why={why} whyNote={whyNote}
          notice={notice} statusLines={statusLines} />
      </main>
      <div className="foot">Research prototype for demonstration, not a certified navigation system.
        Routes, numbers and advice come from recorded, reproducible runs.</div>
    </div>
  );
}
