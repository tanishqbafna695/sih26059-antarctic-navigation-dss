#!/usr/bin/env python
"""CLI wrapper: python scripts/forecast/run_seasonal.py

Phase 6 seasonal-climatology SIC forecast evaluation (vs persistence, FR-5/6).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.forecast.evaluate_seasonal import main  # noqa: E402

if __name__ == "__main__":
    main()
