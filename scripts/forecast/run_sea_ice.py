#!/usr/bin/env python
"""CLI wrapper: python scripts/forecast/run_sea_ice.py

Phase 6 sea-ice forecast evaluation (ridge vs persistence, FR-5/6/7).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.forecast.evaluate_sea_ice import main  # noqa: E402

if __name__ == "__main__":
    main()
