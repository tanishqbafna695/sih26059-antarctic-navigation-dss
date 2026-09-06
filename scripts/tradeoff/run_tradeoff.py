"""CLI runner for Phase 13 trade-off engine (FR-25, FR-26).

Reads the recorded Phase 12 routing report, builds the per-vessel
comparison table, recommends one route under each navigator priority
profile (sensitivity matrix: the recommendation must move when priorities
move, wherever a real trade-off exists), and writes data/tradeoff/latest.json.

Usage:
    python scripts/tradeoff/run_tradeoff.py [--routing data/routing/latest.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.tradeoff import PRIORITY_PROFILES, build_comparison, recommend  # noqa: E402
from backend.tradeoff.comparison import comparison_markdown  # noqa: E402

DEFAULT_ROUTING = REPO_ROOT / "data" / "routing" / "latest.json"


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Phase 13 trade-off engine")
    ap.add_argument("--routing", default=str(DEFAULT_ROUTING))
    ap.add_argument("--out", default=str(REPO_ROOT / "data" / "tradeoff"))
    args = ap.parse_args(argv)

    print("=== SIH26059 Phase 13 — Route Trade-Off Engine ===")
    routing = json.loads(Path(args.routing).read_text(encoding="utf-8"))
    print(f"routing report: {args.routing} "
          f"(depart day {routing.get('depart_day_index')})")

    report = {"phase": 13, "routing_report": str(args.routing),
              "depart_day_index": routing.get("depart_day_index"),
              "vessels": {}}
    for vid, plan in routing.get("vessels", {}).items():
        if not plan.get("routes"):
            comp = build_comparison({"vessel_id": vid, "routes": {},
                                     "reason": plan.get("reason", "no route"),
                                     "details": plan.get("details", {})})
            print(f"\n--- {vid}: NO ROUTES ({comp['reason']}) ---")
            report["vessels"][vid] = {
                "comparison": comp,
                "recommendations": {p: recommend(comp, p)
                                    for p in PRIORITY_PROFILES}}
            continue
        comp = build_comparison(plan)
        recs = {p: recommend(comp, p) for p in PRIORITY_PROFILES}
        report["vessels"][vid] = {"comparison": comp,
                                  "recommendations": recs}

        print(f"\n--- {vid} (depart {comp['depart_date']}) ---")
        print(comparison_markdown(comp))
        print("sensitivity (profile -> recommended [scores]):")
        for p, r in recs.items():
            if r["recommended"] is None:
                print(f"  {p:<13} -> none ({r['reason']})")
                continue
            sc = ", ".join(f"{k}={v:.2f}" for k, v in r["scores"].items())
            print(f"  {p:<13} -> {r['recommended']} [{sc}]"
                  f"{' TIE' if r['tied'] else ''}")
            for h in r["headline_improvements"]:
                print(f"      {h['metric']}: {h['delta_pct']:+.1f}% vs "
                      f"{h['vs_route']}")
            for c in r["caveats"]:
                print(f"      caveat: {c}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved trade-off report to: {out_path}")


if __name__ == "__main__":
    main()
