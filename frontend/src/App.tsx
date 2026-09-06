import { useState, useEffect, useRef, useCallback } from "react";
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
import hazard45 from "./data/hazard_45_pc7.png";
import ice000 from "./data/ice_000.png";
import ice005 from "./data/ice_005.png";
import ice010 from "./data/ice_010.png";
import ice015 from "./data/ice_015.png";
import ice020 from "./data/ice_020.png";
import ice025 from "./data/ice_025.png";
import ice030 from "./data/ice_030.png";
import ice035 from "./data/ice_035.png";
import ice040 from "./data/ice_040.png";
import ice045 from "./data/ice_045.png";
import ice050 from "./data/ice_050.png";
import ice055 from "./data/ice_055.png";
import ice060 from "./data/ice_060.png";
import ice065 from "./data/ice_065.png";
import ice070 from "./data/ice_070.png";
import ice075 from "./data/ice_075.png";
import ice080 from "./data/ice_080.png";
import ice085 from "./data/ice_085.png";
import ice090 from "./data/ice_090.png";
import ice095 from "./data/ice_095.png";
import ice100 from "./data/ice_100.png";
import ice105 from "./data/ice_105.png";

/* ── Ice frame timeline ──────────────────────────────── */
const ICE_FRAMES: { src: string; day: number; date: string }[] = [
  { src: ice000, day: 0,   date: "2019-12-20" },
  { src: ice005, day: 5,   date: "2019-12-25" },
  { src: ice010, day: 10,  date: "2019-12-30" },
  { src: ice015, day: 15,  date: "2020-01-04" },
  { src: ice020, day: 20,  date: "2020-01-09" },
  { src: ice025, day: 25,  date: "2020-01-14" },
  { src: ice030, day: 30,  date: "2020-01-19" },
  { src: ice035, day: 35,  date: "2020-01-24" },
  { src: ice040, day: 40,  date: "2020-01-29" },
  { src: ice045, day: 45,  date: "2020-02-03" },
  { src: ice050, day: 50,  date: "2020-02-08" },
  { src: ice055, day: 55,  date: "2020-02-13" },
  { src: ice060, day: 60,  date: "2020-02-18" },
  { src: ice065, day: 65,  date: "2020-02-23" },
  { src: ice070, day: 70,  date: "2020-02-28" },
  { src: ice075, day: 75,  date: "2020-03-04" },
  { src: ice080, day: 80,  date: "2020-03-09" },
  { src: ice085, day: 85,  date: "2020-03-14" },
  { src: ice090, day: 90,  date: "2020-03-19" },
  { src: ice095, day: 95,  date: "2020-03-24" },
  { src: ice100, day: 100, date: "2020-03-29" },
  { src: ice105, day: 105, date: "2020-04-03" },
];

/* Pre-computed ice-covered fractions (all cells basis) per frame */
const ICE_FRACTIONS = [
  19.0, 17.8, 16.5, 15.1, 13.8, 12.5, 11.4, 10.3, 9.3, 8.4,
  7.5, 6.8, 6.1, 5.5, 5.0, 4.5, 4.1, 3.7, 3.3, 3.0, 2.7, 2.3,
];

type VesselId = "polar_class_pc7" | "polar_class_pc1" | "open_water_rv";
type Scenario = "plan" | "A" | "B";

const COLORS: Record<string, string> = {
  fastest: "#ff9d66",
  safest: "#5ce08a",
  balanced: "#6fb7ff",
};

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
  const [frameIdx, setFrameIdx] = useState(1); // default to Dec 25 (day 5)
  const [playing, setPlaying] = useState(false);
  const playRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const effScenario: Scenario = vessel === "polar_class_pc7" ? scenario : "plan";
  const currentIce = ICE_FRAMES[frameIdx];

  /* ── Ice animation ─────────────────────────────────── */
  const advanceFrame = useCallback(() => {
    setFrameIdx((prev) => (prev + 1) % ICE_FRAMES.length);
  }, []);

  useEffect(() => {
    if (playing) {
      playRef.current = setInterval(advanceFrame, 800);
      return () => { if (playRef.current) clearInterval(playRef.current); };
    } else {
      if (playRef.current) clearInterval(playRef.current);
    }
  }, [playing, advanceFrame]);

  const togglePlay = () => setPlaying((p) => !p);

  /* ── Tradeoff data ─────────────────────────────────── */
  const tradeoff = tradeoffBundle as unknown as Record<string, {
    comparison: { routes_available: boolean; reason?: string; rows: CompRow[];
      confidence: { overall_confidence: number; status_label: string } };
    recommendations: Record<string, { recommended: string }>;
  }>;
  const comp = tradeoff[vessel].comparison;

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
    parityNote = `Live recomputation under "${profile}" ${rec.winner === recorded ? "matches" : "DIFFERS FROM"} the recorded engine (${recorded}).`;
  }

  /* ── Map lines ─────────────────────────────────────── */
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

  /* ── Icebergs ──────────────────────────────────────── */
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

  /* ── Side panel data ───────────────────────────────── */
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

  /* ── KPI values ────────────────────────────────────── */
  const confidencePct = (status.confidence.overall_confidence * 100).toFixed(0);
  const winnerTime = rows.find((r) => r.route === winner)?.time_h.toFixed(1) ?? "—";
  const winnerFuel = rows.find((r) => r.route === winner)?.fuel_l.toLocaleString() ?? "—";
  const icePct = ICE_FRACTIONS[frameIdx].toFixed(1);

  return (
    <div>
      <header>
        <h1>🧊 Antarctic Navigation DSS — Live Demo</h1>
        <div className="sub">
          <span className="live-dot" /> Satellite ice in, three explained route options out.
          A human navigator always decides. Corridor: {corridor.from.name} → {corridor.to.name}.
          All numbers computed by the system.
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
              Update A: new observations{vessel !== "polar_class_pc7" ? " (PC7 only)" : ""}</option>
            <option value="B" disabled={vessel !== "polar_class_pc7"}>
              Update B: iceberg alarm (ASSUMED){vessel !== "polar_class_pc7" ? " (PC7 only)" : ""}</option>
          </select>
        </label>
        <label>Priorities
          <select value={profile} onChange={(e) => setProfile(e.target.value)}
            disabled={effScenario !== "plan"}>
            {Object.keys(PRIORITY_PROFILES).map((p) => (
              <option key={p} value={p}>{p.replace("_", " ")}</option>))}
          </select>
        </label>
        <span className="separator" />
        <label className="chk"><input type="checkbox" checked={showIce}
          onChange={(e) => setShowIce(e.target.checked)} /> ice</label>
        {effScenario === "plan" && vessel === "polar_class_pc7" && (
          <label className="chk"><input type="checkbox" checked={showHazard}
            onChange={(e) => setShowHazard(e.target.checked)} /> hazard</label>)}
        <label className="chk"><input type="checkbox" checked={showBergs}
          onChange={(e) => setShowBergs(e.target.checked)} /> icebergs</label>
        <span className="separator" />
        {effScenario === "plan" && !noRouteReason && ["fastest", "safest", "balanced"].map((n) => (
          <label className="chk" key={n}>
            <input type="checkbox" checked={showRoutes[n] ?? true}
              onChange={(e) => setShowRoutes({ ...showRoutes, [n]: e.target.checked })} />
            <span className="dot" style={{ background: COLORS[n], color: COLORS[n] }} /> {n}
          </label>))}
      </div>

      <main>
        {/* ── Map card ──────────────────────────────── */}
        <div className="card map-card">
          <MapView
            iceUrl={ICE_FRAMES[frameIdx].src}
            showIce={showIce}
            hazardUrl={effScenario === "plan" && vessel === "polar_class_pc7" ? hazard45 : null}
            showHazard={showHazard}
            lines={lines}
            oldLine={oldLine}
            bergs={bergs}
            showBergs={showBergs}
            bbox={corridor.bbox as [[number, number], [number, number]]}
          />

          {/* ── Ice timeline ────────────────────────── */}
          <div className="ice-timeline">
            <button className={`play-btn ${playing ? "playing" : ""}`} onClick={togglePlay}
              title={playing ? "Pause animation" : "Play ice animation"}>
              {playing ? "⏸" : "▶"}
            </button>
            <span className="date-label">{currentIce.date}</span>
            <input type="range" min={0} max={ICE_FRAMES.length - 1} value={frameIdx}
              onChange={(e) => { setFrameIdx(Number(e.target.value)); setPlaying(false); }} />
            <span className="melt-stat">
              <span className="pct">{icePct}%</span><br />ice cover
            </span>
          </div>

          {/* ── Ice melt sparkline ─────────────────── */}
          <div className="sparkline" title="Sea-ice retreat over the season (all cells)">
            {ICE_FRACTIONS.map((f, i) => (
              <div key={i} className="bar" style={{
                height: `${(f / 20) * 100}%`,
                background: i === frameIdx
                  ? "var(--accent-cyan)"
                  : `rgba(77, 166, 255, ${0.15 + 0.45 * (f / 20)})`,
                boxShadow: i === frameIdx ? "0 0 6px var(--accent-cyan)" : undefined,
              }} />
            ))}
          </div>

          <div className="map-note">
            White/bright = solid ice, blue = open water, grey = continental land mass.
            {effScenario !== "plan" ? " Grey dashes = previous course, green = new advice." : ""}
          </div>

          <div className="legend">
            {["fastest", "safest", "balanced"].map((n) => (
              <span key={n} className="legend-item">
                <span className="legend-line" style={{
                  background: showRoutes[n]
                    ? COLORS[n] : "rgba(60,80,100,0.3)",
                }} />
                <span style={{ color: showRoutes[n] ? COLORS[n] : "var(--text-dim)" }}>{n}</span>
              </span>
            ))}
            <span className="legend-item">
              <span className="legend-dot" style={{ background: "#ffd166" }} /> Bharati
            </span>
            <span className="legend-item">
              <span className="legend-dot" style={{ background: "#ff7d9c" }} /> Maitri
            </span>
          </div>
        </div>

        {/* ── Side panel ────────────────────────────── */}
        <div className="panel-card">
          {/* ── KPI strip ──────────────────────────── */}
          <div className="kpi-strip">
            <div className="kpi">
              <div className="value cyan">{winnerTime}{winnerTime !== "—" ? "h" : ""}</div>
              <div className="label">Recommended Time</div>
            </div>
            <div className="kpi">
              <div className="value orange">{winnerFuel}{winnerFuel !== "—" ? " L" : ""}</div>
              <div className="label">Fuel Estimate</div>
            </div>
            <div className="kpi">
              <div className="value green">{confidencePct}%</div>
              <div className="label">Confidence</div>
            </div>
            <div className="kpi">
              <div className="value blue">{icePct}%</div>
              <div className="label">Ice Cover</div>
            </div>
          </div>

          {/* ── Confidence gauge ───────────────────── */}
          <div className="confidence-gauge">
            <svg width="52" height="52" viewBox="0 0 52 52">
              <circle cx="26" cy="26" r="22" fill="none"
                stroke="rgba(30,50,80,0.5)" strokeWidth="5" />
              <circle cx="26" cy="26" r="22" fill="none"
                stroke={status.confidence.overall_confidence > 0.5 ? "var(--accent-cyan)" :
                  status.confidence.overall_confidence > 0.3 ? "var(--accent-orange)" : "var(--accent-red)"}
                strokeWidth="5" strokeLinecap="round"
                strokeDasharray={`${status.confidence.overall_confidence * 138.2} 138.2`}
                transform="rotate(-90 26 26)"
                style={{ transition: "stroke-dasharray 0.8s ease" }} />
              <text x="26" y="30" textAnchor="middle" fill="var(--text-primary)"
                fontSize="13" fontWeight="700">
                {confidencePct}
              </text>
            </svg>
            <div className="gauge-text">
              <strong>{status.confidence.status_label}</strong><br />
              System confidence across all route options
            </div>
          </div>

          <SidePanel tab={tab} setTab={setTab} rows={tableRows}
            winner={effScenario === "plan" ? winner : null}
            parityNote={effScenario === "plan" ? parityNote : null}
            noRouteReason={noRouteReason} why={why} whyNote={whyNote}
            notice={notice} statusLines={statusLines} />
        </div>
      </main>

      <div className="foot">
        Research prototype for demonstration, not a certified navigation system.
        Routes, numbers and advice come from recorded, reproducible runs.
        Built for Smart India Hackathon 2026.
      </div>
    </div>
  );
}
