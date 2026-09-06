/**
 * Client-side port of backend/tradeoff/recommend.py scoring.
 * Same profiles, same min-max math, same "balanced" tie-break, so the UI
 * recomputes the recommendation live AND can verify itself against the
 * recorded engine output (parity badge in the panel).
 */
import type { ComparisonRow, MetricKey } from "./types";

export const SCORE_METRICS: MetricKey[] = [
  "risk",
  "time_h",
  "fuel_l",
  "ice_exp",
  "berg",
];

export const PRIORITY_PROFILES: Record<string, Record<MetricKey, number>> = {
  balanced: { risk: 0.4, time_h: 0.25, fuel_l: 0.2, ice_exp: 0.1, berg: 0.05 },
  safety_first: { risk: 0.7, time_h: 0.1, fuel_l: 0.1, ice_exp: 0.05, berg: 0.05 },
  time_first: { risk: 0.1, time_h: 0.7, fuel_l: 0.1, ice_exp: 0.05, berg: 0.05 },
  fuel_saver: { risk: 0.15, time_h: 0.1, fuel_l: 0.65, ice_exp: 0.05, berg: 0.05 },
};

export interface RecResult {
  winner: string;
  scores: Record<string, number>;
  tied: boolean;
}

export function recommend(
  rows: ComparisonRow[],
  profile: string
): RecResult {
  const weights = PRIORITY_PROFILES[profile];
  if (!weights) throw new Error(`unknown profile ${profile}`);
  const norm: Record<string, Record<MetricKey, number>> = {};
  for (const m of SCORE_METRICS) {
    const vals = rows.map((r) => r[m]);
    const lo = Math.min(...vals);
    const hi = Math.max(...vals);
    const span = hi - lo;
    for (const r of rows) {
      if (!norm[r.route]) norm[r.route] = {} as Record<MetricKey, number>;
      norm[r.route][m] = span <= 0 ? 0 : (r[m] - lo) / span;
    }
  }
  const scores: Record<string, number> = {};
  for (const r of rows) {
    scores[r.route] = SCORE_METRICS.reduce(
      (s, m) => s + weights[m] * norm[r.route][m],
      0
    );
  }
  const best = Math.min(...Object.values(scores));
  const tied = Object.keys(scores).filter((r) => scores[r] === best);
  // NOTE: backend compares unrounded floats; the bundle carries recorded
  // scores, so near-ties can differ in the last digit. The tie-break rule
  // itself ("balanced" on exact tie) is identical.
  const winner =
    tied.length > 1 && tied.includes("balanced") ? "balanced" : tied[0];
  return { winner, scores, tied: tied.length > 1 };
}
