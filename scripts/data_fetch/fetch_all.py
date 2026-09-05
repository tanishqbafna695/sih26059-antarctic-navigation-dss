#!/usr/bin/env python
"""CLI wrapper: python scripts/data_fetch/fetch_all.py --synthetic

Delegates to backend.data_pipeline.fetch.fetch_all (Phase 4 pipeline).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.data_pipeline.fetch.fetch_all import main  # noqa: E402

if __name__ == "__main__":
    main()