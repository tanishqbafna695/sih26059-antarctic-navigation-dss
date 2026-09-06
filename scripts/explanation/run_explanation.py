"""CLI runner for Phase 14 explanation engine (FR-27, FR-28 demo shape).

Reads the recorded Phase 13 trade-off report, explains each vessel's
balanced-profile recommendation with vessel-fit + confidence (FR-27), and
demonstrates the FR-28 change-explanation shape on a recorded old/new pair
(real re-route pairs arrive in Phase 15). Writes data/explanation/latest.json.

Usage:
    python scripts/explanation/run_explanation.py [--tradeoff data/tradeoff/latest.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.explanation import explain_change, explain_recommendation  # noqa: E402
from backend.vessel import VesselRegistry  # noqa: E402

DEFAULT_TRADEOFF = REPO_ROOT / "data" / "tradeoff" / "latest.json"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Phase 14 explanation engine")
    ap.add_argument("--tradeoff", default=str(DEFAULT_TRADEOFF))
    ap.add_argument("--out", default=str(REPO_ROOT / "data" / "explanation"))
    args = ap.parse_args(argv)

    print("=== SIH26059 Phase 14 — Explanation Engine ===")
    tradeoff = json.loads(Path(args.tradeoff).read_text(encoding="utf-8"))
    registry = VesselRegistry()

    report = {"phase": 14, "tradeoff_report": str(args.tradeoff), "vessels": {}}
    for vid, t in tradeoff.get("vessels", {}).items():
        comp = t.get("comparison", {})
        rec = t.get("recommendations", {}).get("balanced")
        if rec is None or not comp.get("routes_available"):
            exp = {"explained": False,
                   "reason": comp.get("reason", "no routes available"),
                   "text": f"No explanation: {comp.get('reason', 'no routes')}."}
            print(f"\n--- {vid}: no explanation ({exp['reason']}) ---")
            report["vessels"][vid] = {"explanation": exp, "change_demo": None}
            continue
        try:
            prof = registry.get_profile(vid)
            vessel = {"name": prof.name, "ice_class": prof.ice_class,
                      "max_sic_limit": prof.max_sic_limit}
        except KeyError:
            vessel = {"name": comp.get("vessel_id", vid),
                      "ice_class": "unknown", "max_sic_limit": 1.0}
        exp = explain_recommendation(comp["rows"], rec, vessel)
        print(f"\n--- {vid} ---\n{exp['text']}")

        # FR-28 shape demo on recorded numbers: yesterday's fastest-priority
        # answer vs today's balanced answer for the same vessel.
        change_demo = None
        recs = t.get("recommendations", {})
        if "time_first" in recs and recs["time_first"].get("recommended"):
            by_name = {r["route"]: r for r in comp["rows"]}
            o, n = recs["time_first"]["recommended"], rec["recommended"]
            change_demo = explain_change(
                {"recommended": o, **{m: by_name[o][m] for m in
                                      ("travel_time_h", "fuel_liters", "mean_hazard")}},
                {"recommended": n, **{m: by_name[n][m] for m in
                                      ("travel_time_h", "fuel_liters", "mean_hazard")}},
                trigger="priority shift time_first -> balanced (demo shape; "
                        "environmental triggers arrive in Phase 15)")
            print(f"\n[change demo]\n{change_demo['text']}")
        report["vessels"][vid] = {"explanation": exp, "change_demo": change_demo}

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved explanation report to: {out_path}")


if __name__ == "__main__":
    main()
