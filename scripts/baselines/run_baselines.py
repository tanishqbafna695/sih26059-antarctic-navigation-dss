#!/usr/bin/env python
"""CLI wrapper: python scripts/baselines/run_baselines.py

Runs the Phase 5 baseline evaluation (FR-6/9/21) on the feature store and
writes a reproducible JSON report under data/baselines/.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.baselines.evaluate import main  # noqa: E402

if __name__ == "__main__":
    main()
