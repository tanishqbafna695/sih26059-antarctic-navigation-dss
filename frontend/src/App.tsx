import { useState, useCallback, useRef, useEffect } from "react";
import MapView, { type RouteLine } from "./components/MapView";
import Sidebar from "./components/Sidebar";
import { CORRIDORS, type CorridorTradeoff, type CorridorStatus, type RouteRow } from "./lib/corridors";
import { getTradeoff, getExplanations, getRoutes, getStatus, getBergs } from "./lib/corridorData";
import { recommend } from "./lib/scoring";
import iceFrames from "./data/ice_index.json";

type VesselId = "polar_class_pc7" | "polar_class_pc1" | "open_water_rv";

const COLORS: Record<string, string> = {
  fastest: "#ff9d66",
  safest: "#5ce08a",
  balanced: "#6fb7ff",
};

/* ── Ice frame imports (all 22 frames) ──────────────────── */
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

const ICE_SOURCES: string[] = [
  ice000, ice005, ice010, ice015, ice020, ice025, ice030, ice035,
  ice040, ice045, ice050, ice055, ice060, ice065, ice070, ice075,
  ice080, ice085, ice090, ice095, ice100, ice105,
];

interface IceFrame {
  src: string;
  day: number;
  date: string;
  ice_pct: number;
}

const ICE_FRAMES: IceFrame[] = (iceFrames as { day: number; date: string; ice_pct: number }[]).map(
  (f, i) => ({ ...f, src: ICE_SOURCES[i] })
);

export default function App() {
  /* ── State ─────────────────────────────────────────────── */
  const [corridorId, setCorridorId] = useState("bharati_maitri");
  const [vessel, setVessel] = useState<VesselId>("polar_class_pc7");
  const [profile, setProfile] = useState("balanced");
  const [frameIdx, setFrameIdx] = useState(1);
  const [playing, setPlaying] = useState(false);
  const [showIce, setShowIce] = useState(true);
  const [showRoutes, setShowRoutes] = useState<Record<string, boolean>>({
    fastest: true, safest: true, balanced: true,
  });
  const [customFrom, setCustomFrom] = useState("");
  const [customTo, setCustomTo] = useState("");
  const [isCustom, setIsCustom] = useState(false);
  const playRef = useRef<ReturnType<typeof setInterval> | null>(null);

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

  const currentFrame = ICE_FRAMES[frameIdx];

  /* ── Load corridor data ────────────────────────────────── */
  const corridor = CORRIDORS.find((c) => c.id === corridorId) ?? CORRIDORS[0];
  const allTradeoffs = getTradeoff(corridor.id) as Record<string, CorridorTradeoff>;
  const tradeoff: CorridorTradeoff = allTradeoffs[vessel] ?? allTradeoffs.polar_class_pc7 ?? ({} as CorridorTradeoff);
  const explanations = getExplanations(corridor.id) as Record<string, unknown>;
  const routesData = getRoutes(corridor.id) as Record<string, Record<string, Record<string, { coords: number[][] }>>>;
  const status = getStatus(corridor.id) as CorridorStatus;
  const bergsData = getBergs(corridor.id) as Array<{ lon: number; lat: number; label: string; buffer_poly: number[][][] }>;

  const comp = tradeoff?.comparison ?? { routes_available: false, rows: [], confidence: { overall_confidence: 0, status_label: 'NO DATA' } };
  const winner = comp.routes_available
    ? (() => {
        const scoreRows = comp.rows
          .filter((r) => ["fastest", "safest", "balanced"].includes(r.route))
          .map((r) => ({
            route: r.route, time_h: r.travel_time_h, fuel_l: r.fuel_liters,
            risk: r.mean_hazard, ice_exp: r.ice_exposure_frac * 100,
            berg: r.mean_iceberg_hazard,
          }));
        return recommend(scoreRows, profile).winner;
      })()
    : null;

  const rows: RouteRow[] = comp.routes_available ? comp.rows : [];

  /* ── Map lines ─────────────────────────────────────────── */
  let lines: RouteLine[] = [];
  if (comp.routes_available) {
    const vesselRoutes = routesData?.plan45?.[vessel] ?? routesData?.plan45?.polar_class_pc7;
    if (vesselRoutes) {
      lines = ["fastest", "safest", "balanced"].map((n) => ({
        id: n,
        coords: vesselRoutes[n]?.coords ?? [],
        color: COLORS[n],
        width: n === winner ? 4 : 2.5,
        dashed: n !== winner,
        visible: showRoutes[n] ?? true,
      }));
    }
  }

  /* ── Bergs ─────────────────────────────────────────────── */
  const bergs = {
    buffers: {
      type: "FeatureCollection" as const,
      features: bergsData.map((b) => ({
        type: "Feature" as const,
        properties: {},
        geometry: { type: "Polygon" as const, coordinates: b.buffer_poly },
      })),
    },
    fixes: {
      type: "FeatureCollection" as const,
      features: bergsData.map((b) => ({
        type: "Feature" as const,
        properties: {},
        geometry: { type: "Point" as const, coordinates: [b.lon, b.lat] },
      })),
    },
  };

  /* ── Custom corridor handler ───────────────────────────── */
  const handleApplyCustom = () => {
    if (!customFrom || !customTo || customFrom === customTo) return;
    setIsCustom(true);
    // In a real system, this would call the API.
    // For the demo, we use the nearest existing corridor.
    setCorridorId("bharati_maitri");
  };

  return (
    <div className="app-root">
      {/* ── Top bar ────────────────────────────────── */}
      <header className="topbar">
        <div className="topbar-left">
          <span className="logo">🧊</span>
          <h1>Antarctic Navigation DSS</h1>
          <span className="badge">DEMO</span>
        </div>
        <div className="topbar-center">
          <span className="live-dot" />
          <span className="topbar-info">
            {corridor.from.name} → {corridor.to.name} &nbsp;·&nbsp;
            {corridor.distance_km.toLocaleString()} km &nbsp;·&nbsp;
            {currentFrame.date}
          </span>
        </div>
        <div className="topbar-right">
          <span className="topbar-stat">
            <span className="topbar-stat-value cyan">{currentFrame.ice_pct.toFixed(1)}%</span>
            <span className="topbar-stat-label">ICE</span>
          </span>
          <span className="topbar-stat">
            <span className={`topbar-stat-value ${status.confidence.overall_confidence > 0.3 ? "green" : "orange"}`}>
              {(status.confidence.overall_confidence * 100).toFixed(0)}%
            </span>
            <span className="topbar-stat-label">CONF</span>
          </span>
        </div>
      </header>

      {/* ── Main layout ────────────────────────────── */}
      <div className="main-layout">
        {/* Sidebar */}
        <Sidebar
          corridors={CORRIDORS}
          selectedCorridor={corridorId}
          onSelectCorridor={(id) => { setCorridorId(id); setIsCustom(false); }}
          vessel={vessel}
          onSelectVessel={(v) => setVessel(v as VesselId)}
          profile={profile}
          onSelectProfile={setProfile}
          tradeoff={tradeoff}
          explanation={(explanations[vessel] ?? {}) as Record<string, unknown>}
          winner={winner}
          rows={rows}
          status={status}
          showIce={showIce}
          onToggleIce={setShowIce}
          showRoutes={showRoutes}
          onToggleRoute={(n, v) => setShowRoutes({ ...showRoutes, [n]: v })}
          customFrom={customFrom}
          customTo={customTo}
          onSetCustomFrom={setCustomFrom}
          onSetCustomTo={setCustomTo}
          onApplyCustom={handleApplyCustom}
          isCustom={isCustom}
        />

        {/* Map area */}
        <div className="map-area">
          <MapView
            iceUrl={currentFrame.src}
            showIce={showIce}
            hazardUrl={null}
            showHazard={false}
            lines={lines}
            oldLine={null}
            bergs={bergs}
            showBergs={true}
            bbox={corridor.bbox}
          />

          {/* Ice timeline */}
          <div className="ice-timeline-bar">
            <button
              className={`play-btn ${playing ? "playing" : ""}`}
              onClick={() => setPlaying(!playing)}
            >
              {playing ? "⏸" : "▶"}
            </button>
            <span className="date-label">{currentFrame.date}</span>
            <input
              type="range" min={0} max={ICE_FRAMES.length - 1} value={frameIdx}
              onChange={(e) => { setFrameIdx(Number(e.target.value)); setPlaying(false); }}
            />
            <span className="melt-pct">{currentFrame.ice_pct.toFixed(1)}%</span>
          </div>

          {/* Sparkline */}
          <div className="sparkline-bar">
            {ICE_FRAMES.map((f, i) => (
              <div key={i} className={`spark-col ${i === frameIdx ? "active" : ""}`}
                style={{
                  height: `${(f.ice_pct / 20) * 100}%`,
                  background: i === frameIdx
                    ? "var(--accent-cyan)"
                    : `rgba(77, 166, 255, ${0.15 + 0.5 * (f.ice_pct / 20)})`,
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* ── Bottom status bar ──────────────────────── */}
      <footer className="statusbar">
        <span>Research prototype · Not a certified navigation system</span>
        <span>·</span>
        <span>All routes require human review</span>
        <span>·</span>
        <span>Built for Smart India Hackway 2026</span>
      </footer>
    </div>
  );
}
