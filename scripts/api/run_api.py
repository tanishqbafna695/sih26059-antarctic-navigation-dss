"""Run the Phase 18 Antarctic Navigation DSS API server.

Usage:
    python scripts/api/run_api.py                 # default: localhost:8000
    python scripts/api/run_api.py --port 8080     # custom port
    python scripts/api/run_api.py --check         # smoke-test endpoints, then exit

The server serves the full decision-support chain (FR-33) against the
recorded feature store and report artifacts, fully offline (FR-34).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def smoke_test(base_url: str) -> None:
    """Hit every endpoint once and print the JSON status."""
    import urllib.request
    import urllib.error

    endpoints = [
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/vessels"),
        ("GET", "/api/v1/corridors"),
        ("GET", "/api/v1/validation"),
    ]
    for method, path in endpoints:
        url = base_url + path
        try:
            req = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                print(f"  {method:4s} {path:30s} -> {resp.status}  "
                      f"({len(json.dumps(data))} bytes)")
        except Exception as e:
            print(f"  {method:4s} {path:30s} -> ERROR: {e}")

    # POST /plan
    plan_payload = {
        "origin": {"lat": -69.41, "lon": 76.19},
        "destination": {"lat": -70.77, "lon": 11.73},
        "vessel_id": "polar_class_pc7",
        "depart_day_index": 45,
        "priority": "balanced",
    }
    url = base_url + "/api/v1/plan"
    try:
        body = json.dumps(plan_payload).encode()
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            routes = list(data.get("routes", {}).keys())
            rec = data.get("recommendation", {}).get("recommended", "?")
            print(f"  POST /api/v1/plan                -> {resp.status}  "
                  f"routes={routes} recommendation={rec}")
    except Exception as e:
        print(f"  POST /api/v1/plan                -> ERROR: {e}")

    print("Smoke test complete.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Phase 18 API server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--check", action="store_true",
                    help="Smoke-test all endpoints then exit")
    args = ap.parse_args()

    if args.check:
        print("Running smoke test against http://{}:{}...".format(
            args.host, args.port))
        smoke_test(f"http://{args.host}:{args.port}")
        return

    import uvicorn
    from backend.api.app import create_app
    app = create_app()
    print(f"Starting Antarctic DSS API at http://{args.host}:{args.port}")
    print(f"Docs: http://{args.host}:{args.port}/docs")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
