"""Compatibility wrapper.

The repository historically included a separate pipeline script at `codes/index.py`.
To keep a single source of truth, this file now forwards to the unified DMS CLI.

Usage:
  python codes/index.py init-db
  python codes/index.py index --dir <folder>
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path when running as `python codes/index.py ...`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from dms.cli import main



if __name__ == "__main__":
    raise SystemExit(main())

