export type PanelTab = "routes" | "why" | "status";

interface TableRow {
  route: string;
  time_h: number;
  fuel_l: number;
  risk: number;
  ice_exp_pct: number;
}

interface WhyData {
  headline: string;
  strengths: string[];
  prices: string[];
  vessel_statement: string;
  confidence_note: string;
  caveats: string[];
}

interface SidePanelProps {
  tab: PanelTab;
  setTab: (t: PanelTab) => void;
  rows: TableRow[];
  winner: string | null;
  parityNote: string | null;
  noRouteReason: string | null;
  why: WhyData | null;
  whyNote: string | null;
  notice: { outcome: string; trigger: string; change_text: string } | null;
  statusLines: string[];
}

export default function SidePanel(p: SidePanelProps) {
  return (
    <div className="card">
      <div className="tabs">
        {(["routes", "why", "status"] as PanelTab[]).map((t) => (
          <button key={t} className={p.tab === t ? "active" : ""}
            onClick={() => p.setTab(t)}>
            {t === "routes" ? "Routes" : t === "why" ? "Why this advice" : "Data status"}
          </button>
        ))}
      </div>
      {p.tab === "routes" && (
        p.noRouteReason ? <div className="warn">No acceptable route: {p.noRouteReason}</div> :
        <table>
          <thead><tr><th>Option</th><th>Time</th><th>Fuel</th><th>Risk</th><th>Ice on path</th></tr></thead>
          <tbody>
            {p.rows.map((r) => (
              <tr key={r.route} className={r.route === p.winner ? "winner" : ""}>
                <td>{r.route}{r.route === p.winner ? " ★" : ""}</td>
                <td>{r.time_h.toFixed(1)} h</td>
                <td>{r.fuel_l.toLocaleString()} L</td>
                <td>{r.risk.toFixed(3)}</td>
                <td>{r.ice_exp_pct.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {p.tab === "routes" && p.parityNote && <div className="note">{p.parityNote}</div>}
      {p.tab === "routes" && p.notice && (
        <div className="notice">
          <b>Re-route {p.notice.outcome}.</b> Trigger: {p.notice.trigger}
          <pre>{p.notice.change_text}</pre>
        </div>
      )}
      {p.tab === "why" && (
        p.why ? <>
          <p><b>{p.why.headline}</b></p>
          <ul>{p.why.strengths.map((s, i) => <li key={i}>✓ {s}</li>)}</ul>
          <p className="plain">The price of this choice:</p>
          <ul>{p.why.prices.map((s, i) => <li key={i}>{s}</li>)}</ul>
          <p className="plain">{p.why.vessel_statement}</p>
          <p className="plain">{p.why.confidence_note}</p>
          {p.why.caveats.map((c, i) => <div className="note" key={i}>Caveat: {c}</div>)}
          {p.whyNote && <div className="note">{p.whyNote}</div>}
        </> : <div className="warn">No advice to explain{p.noRouteReason ? `: ${p.noRouteReason}` : "."}</div>
      )}
      {p.tab === "status" && (
        <ul>{p.statusLines.map((s, i) => <li key={i}>{s}</li>)}</ul>
      )}
    </div>
  );
}
