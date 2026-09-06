import { useState } from "react";
import {
  type CorridorMeta,
  type RouteRow,
  type CorridorTradeoff,
  ALL_STATIONS,
} from "../lib/corridors";
import { PRIORITY_PROFILES } from "../lib/scoring";

export type PanelTab = "routes" | "why" | "compare";

interface SidebarProps {
  corridors: CorridorMeta[];
  selectedCorridor: string;
  onSelectCorridor: (id: string) => void;
  vessel: string;
  onSelectVessel: (v: string) => void;
  profile: string;
  onSelectProfile: (p: string) => void;
  tradeoff: CorridorTradeoff;
  explanation: Record<string, unknown>;
  winner: string | null;
  rows: RouteRow[];
  status: { confidence: { overall_confidence: number; status_label: string } };
  showIce: boolean;
  onToggleIce: (v: boolean) => void;
  showRoutes: Record<string, boolean>;
  onToggleRoute: (name: string, v: boolean) => void;
  // Custom corridor
  customFrom: string;
  customTo: string;
  onSetCustomFrom: (name: string) => void;
  onSetCustomTo: (name: string) => void;
  onApplyCustom: () => void;
  isCustom: boolean;
}

function formatHours(h: number): string {
  if (h >= 100) return `${Math.round(h)}h`;
  return `${h.toFixed(1)}h`;
}

function formatFuel(l: number): string {
  if (l >= 100000) return `${(l / 1000).toFixed(0)}k L`;
  if (l >= 10000) return `${(l / 1000).toFixed(1)}k L`;
  return `${Math.round(l)} L`;
}

export default function Sidebar(p: SidebarProps) {
  const [tab, setTab] = useState<PanelTab>("routes");
  const [showCustom, setShowCustom] = useState(false);

  const comp = p.tradeoff.comparison;
  const explanation = p.explanation as Record<string, unknown>;
  const routeRows = p.rows;

  const confPct = (p.status.confidence.overall_confidence * 100).toFixed(0);

  return (
    <div className="sidebar">
      {/* ── Corridor selector ──────────────────── */}
      <div className="sb-section">
        <div className="sb-section-title">🗺️ CORRIDOR</div>
        <div className="corridor-list">
          {p.corridors.map((c) => (
            <button
              key={c.id}
              className={`corridor-btn ${c.id === p.selectedCorridor ? "active" : ""}`}
              onClick={() => p.onSelectCorridor(c.id)}
            >
              <span className="corridor-name">{c.name}</span>
              <span className="corridor-dist">{c.distance_km.toLocaleString()} km</span>
            </button>
          ))}
        </div>

        {/* Custom origin/destination */}
        {!showCustom ? (
          <button className="custom-toggle" onClick={() => setShowCustom(true)}>
            + Custom corridor
          </button>
        ) : (
          <div className="custom-form">
            <label className="custom-label">
              <span>From</span>
              <select value={p.customFrom} onChange={(e) => p.onSetCustomFrom(e.target.value)}>
                <option value="">Select origin...</option>
                {ALL_STATIONS.map((s) => (
                  <option key={s.name} value={s.name}>{s.name}</option>
                ))}
              </select>
            </label>
            <label className="custom-label">
              <span>To</span>
              <select value={p.customTo} onChange={(e) => p.onSetCustomTo(e.target.value)}>
                <option value="">Select destination...</option>
                {ALL_STATIONS.map((s) => (
                  <option key={s.name} value={s.name}>{s.name}</option>
                ))}
              </select>
            </label>
            <div className="custom-actions">
              <button className="btn-primary" onClick={p.onApplyCustom}
                disabled={!p.customFrom || !p.customTo || p.customFrom === p.customTo}>
                Compute route
              </button>
              <button className="btn-ghost" onClick={() => setShowCustom(false)}>Cancel</button>
            </div>
          </div>
        )}
      </div>

      {/* ── Vessel & profile ───────────────────── */}
      <div className="sb-section">
        <div className="sb-section-title">🚢 VESSEL & PRIORITY</div>
        <label className="sb-label">
          Vessel class
          <select value={p.vessel} onChange={(e) => p.onSelectVessel(e.target.value)}>
            <option value="polar_class_pc7">Polar Class PC7</option>
            <option value="polar_class_pc1">Icebreaker PC1</option>
            <option value="open_water_rv">Open Water RV</option>
          </select>
        </label>
        <label className="sb-label">
          Priority
          <select value={p.profile} onChange={(e) => p.onSelectProfile(e.target.value)}>
            {Object.keys(PRIORITY_PROFILES).map((pr) => (
              <option key={pr} value={pr}>{pr.replace("_", " ")}</option>
            ))}
          </select>
        </label>
      </div>

      {/* ── Quick stats ────────────────────────── */}
      <div className="sb-section">
        <div className="sb-section-title">📊 QUICK STATS</div>
        <div className="quick-stats">
          <div className="stat-row">
            <span className="stat-label">Confidence</span>
            <span className={`stat-value ${p.status.confidence.overall_confidence > 0.5 ? "green" : p.status.confidence.overall_confidence > 0.2 ? "orange" : "red"}`}>
              {confPct}% {p.status.confidence.status_label}
            </span>
          </div>
          {comp.routes_available && routeRows.length > 0 && (
            <>
              <div className="stat-row">
                <span className="stat-label">Best time</span>
                <span className="stat-value cyan">
                  {formatHours(Math.min(...p.rows.map((r) => r.travel_time_h)))}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Best fuel</span>
                <span className="stat-value orange">
                  {formatFuel(Math.min(...p.rows.map((r) => r.fuel_liters)))}
                </span>
              </div>
              <div className="stat-row">
                <span className="stat-label">Lowest risk</span>
                <span className="stat-value green">
                  {(Math.min(...p.rows.map((r) => r.mean_hazard)) * 10000).toFixed(1)}e-4
                </span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Layer toggles ──────────────────────── */}
      <div className="sb-section">
        <div className="sb-section-title">🛰️ LAYERS</div>
        <div className="layer-toggles">
          <label className="toggle-label">
            <input type="checkbox" checked={p.showIce}
              onChange={(e) => p.onToggleIce(e.target.checked)} />
            <span className="toggle-track"><span className="toggle-thumb" /></span>
            Sea ice
          </label>
        </div>
        {comp.routes_available && (
          <div className="layer-toggles">
            {["fastest", "safest", "balanced"].map((n) => (
              <label key={n} className="toggle-label">
                <input type="checkbox" checked={p.showRoutes[n] ?? true}
                  onChange={(e) => p.onToggleRoute(n, e.target.checked)} />
                <span className="toggle-track"><span className="toggle-thumb" /></span>
                <span className={`route-dot ${n}`} />
                {n}
              </label>
            ))}
          </div>
        )}
      </div>

      {/* ── Tabs ───────────────────────────────── */}
      <div className="sb-section sb-tabs-section">
        <div className="sb-tabs">
          <button className={tab === "routes" ? "active" : ""} onClick={() => setTab("routes")}>
            Routes
          </button>
          <button className={tab === "compare" ? "active" : ""} onClick={() => setTab("compare")}>
            Compare
          </button>
          <button className={tab === "why" ? "active" : ""} onClick={() => setTab("why")}>
            Why
          </button>
        </div>

        {/* Routes tab */}
        {tab === "routes" && (
          !comp.routes_available ? (
            <div className="no-route">
              <div className="no-route-icon">🚫</div>
              <div className="no-route-text">{comp.reason ?? "No acceptable route found"}</div>
            </div>
          ) : (
            <div className="route-cards">
              {p.rows.map((r) => (
                <div key={r.route} className={`route-card ${r.route === p.winner ? "winner" : ""}`}>
                  <div className="route-card-header">
                    <span className={`route-badge ${r.route}`}>{r.route}</span>
                    {r.route === p.winner && <span className="winner-badge">★ RECOMMENDED</span>}
                  </div>
                  <div className="route-metrics">
                    <div className="metric">
                      <span className="metric-value cyan">{formatHours(r.travel_time_h)}</span>
                      <span className="metric-label">TIME</span>
                    </div>
                    <div className="metric">
                      <span className="metric-value orange">{formatFuel(r.fuel_liters)}</span>
                      <span className="metric-label">FUEL</span>
                    </div>
                    <div className="metric">
                      <span className="metric-value green">{(r.mean_hazard * 10000).toFixed(1)}</span>
                      <span className="metric-label">RISK ×10⁴</span>
                    </div>
                    <div className="metric">
                      <span className="metric-value blue">{(r.ice_exposure_frac * 100).toFixed(1)}%</span>
                      <span className="metric-label">ICE</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )
        )}

        {/* Compare tab */}
        {tab === "compare" && comp.routes_available && routeRows.length >= 2 && (
          <div className="compare-view">
            <div className="compare-header">Route Comparison</div>
            <table className="compare-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  {routeRows.map((r) => (
                    <th key={r.route} className={r.route === p.winner ? "winner-col" : ""}>
                      {r.route}{r.route === p.winner ? " ★" : ""}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Time</td>
                  {routeRows.map((r) => (
                    <td key={r.route} className={r.route === p.winner ? "winner-col" : ""}>
                      {formatHours(r.travel_time_h)}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td>Fuel</td>
                  {routeRows.map((r) => (
                    <td key={r.route} className={r.route === p.winner ? "winner-col" : ""}>
                      {formatFuel(r.fuel_liters)}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td>Risk</td>
                  {routeRows.map((r) => (
                    <td key={r.route} className={r.route === p.winner ? "winner-col" : ""}>
                      {(r.mean_hazard * 10000).toFixed(1)}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td>Ice on path</td>
                  {routeRows.map((r) => (
                    <td key={r.route} className={r.route === p.winner ? "winner-col" : ""}>
                      {(r.ice_exposure_frac * 100).toFixed(1)}%
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {/* Why tab */}
        {tab === "why" && (
          explanation && (explanation as Record<string, unknown>).explained ? (
            <div className="why-view">
              <p className="why-headline">
                {(explanation as Record<string, string>).headline}
              </p>
              <div className="why-section">
                <div className="why-label">Strengths</div>
                <ul>{((explanation as Record<string, string[]>).strengths ?? []).map((s: string, i: number) => (
                  <li key={i}><span className="green">✓</span> {s}</li>
                ))}</ul>
              </div>
              <div className="why-section">
                <div className="why-label">Trade-offs</div>
                <ul>{((explanation as Record<string, string[]>).prices ?? []).map((s: string, i: number) => (
                  <li key={i}><span className="orange">−</span> {s}</li>
                ))}</ul>
              </div>
              <p className="why-note">{(explanation as Record<string, string>).vessel_statement}</p>
              <p className="why-note">{(explanation as Record<string, string>).confidence_note}</p>
              {((explanation as Record<string, string[]>).caveats ?? []).map((c: string, i: number) => (
                <div key={i} className="caveat">⚠ {c}</div>
              ))}
            </div>
          ) : (
            <div className="no-route">
              <div className="no-route-text">
                {(explanation as Record<string, string>)?.reason ?? "No advice available"}
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
}
