"""Single-command demo launcher for the Antarctic Navigation DSS (Phase 20).

Starts the FastAPI backend + Vite dev server for the React UI, then opens
the browser. Fully offline (NFR-2): no network dependency at judging time.

Usage:
    python scripts/demo/start_demo.py              # default ports
    python scripts/demo/start_demo.py --api-port 8080 --ui-port 5173
    python scripts/demo/start_demo.py --check       # verify readiness, then exit

The operator workflow (NFR-3, < 2 min):
  1. Launch (this script)
  2. Select vessel (PC7 / PC1 / Open Water RV)
  3. Select view (Plan / Update A / Update B)
  4. Select priority (balanced / safety_first / time_first / fuel_saver)
  5. Toggle layers (ice / hazard / icebergs / route visibility)
  6. Inspect Routes tab (trade-off table)
  7. Inspect Why This Advice tab (explanation)
  8. Inspect Data Status tab (confidence, sources, honesty)
  9. Switch to Update B to see the re-route alarm
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def wait_for_server(url: str, timeout: float = 30.0, interval: float = 0.5) -> bool:
    """Poll until the server responds or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status < 500:
                    return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def smoke_test(base_url: str) -> dict:
    """Hit key endpoints and return status dict."""
    results = {}
    endpoints = [
        ("health", "/api/v1/health"),
        ("vessels", "/api/v1/vessels"),
        ("plan_pc7", "/api/v1/plan"),
    ]
    for name, path in endpoints:
        try:
            if path == "/api/v1/plan":
                body = json.dumps({
                    "origin": {"lat": -69.41, "lon": 76.19},
                    "destination": {"lat": -70.77, "lon": 11.73},
                    "vessel_id": "polar_class_pc7",
                    "depart_day_index": 45,
                    "priority": "balanced",
                }).encode()
                req = urllib.request.Request(
                    base_url + path, data=body,
                    headers={"Content-Type": "application/json"}, method="POST")
            else:
                req = urllib.request.Request(base_url + path, method="GET")
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                results[name] = {"status": "ok", "code": resp.status}
                if name == "plan_pc7":
                    results[name]["routes"] = list(data.get("routes", {}).keys())
                    results[name]["recommendation"] = data.get("recommendation", {}).get("recommended")
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="Antarctic DSS Demo Launcher")
    ap.add_argument("--api-port", type=int, default=8000)
    ap.add_argument("--ui-port", type=int, default=5173)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--check", action="store_true",
                    help="Verify readiness then exit (for CI/scripting)")
    args = ap.parse_args()

    api_url = f"http://{args.host}:{args.api_port}"
    ui_url = f"http://{args.host}:{args.ui_port}"

    print("=" * 60)
    print("  Antarctic Ship-Route Advisor — Demo Mode")
    print("  SIH26059 | Offline | Deterministic")
    print("=" * 60)

    # ── Step 1: Start the API server ────────────────────────────────────────
    print(f"\n[1/3] Starting API server on {api_url} ...")
    api_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api.server:app",
         "--host", args.host, "--port", str(args.api_port),
         "--log-level", "warning"],
        cwd=str(ROOT),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    if not wait_for_server(f"{api_url}/api/v1/health", timeout=30):
        print("  ERROR: API server failed to start")
        api_proc.terminate()
        sys.exit(1)
    print("  API server ready.")

    # ── Step 2: Start the UI dev server ─────────────────────────────────────
    print(f"[2/3] Starting UI on {ui_url} ...")
    ui_dir = ROOT / "frontend"
    ui_proc = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(args.ui_port),
         "--host", args.host],
        cwd=str(ui_dir),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=(sys.platform == "win32"),
    )

    if not wait_for_server(ui_url, timeout=30):
        print("  ERROR: UI server failed to start")
        api_proc.terminate()
        ui_proc.terminate()
        sys.exit(1)
    print("  UI server ready.")

    # ── Step 3: Verify ──────────────────────────────────────────────────────
    print(f"[3/3] Verifying API endpoints ...")
    results = smoke_test(api_url)
    for name, r in results.items():
        status = r["status"]
        extra = ""
        if name == "plan_pc7" and status == "ok":
            extra = f" routes={r.get('routes', [])} rec={r.get('recommendation')}"
        print(f"  {name:12s}: {status}{extra}")

    print()
    print("=" * 60)
    print(f"  API:    {api_url}/docs")
    print(f"  UI:     {ui_url}")
    print("=" * 60)
    print()
    print("Operator workflow (NFR-3, < 2 min):")
    print("  1. Open the UI at the URL above")
    print("  2. Select vessel (PC7 / PC1 / Open Water RV)")
    print("  3. Select view (Plan / Update A / Update B)")
    print("  4. Select priority profile")
    print("  5. Toggle layers and inspect routes")
    print("  6. Switch to Update B to see the re-route alarm")
    print()
    print("Press Ctrl+C to stop both servers.")
    print()

    if args.check:
        print("Check mode: all services ready. Stopping servers.")
        api_proc.terminate()
        ui_proc.terminate()
        return

    # ── Keep running until Ctrl+C ───────────────────────────────────────────
    try:
        api_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down ...")
    finally:
        api_proc.terminate()
        ui_proc.terminate()
        try:
            api_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_proc.kill()
        try:
            ui_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            ui_proc.kill()
        print("Servers stopped.")


if __name__ == "__main__":
    main()
