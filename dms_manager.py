"""Backward-compatible entrypoint for the Municipal DMS.

Original project used a single-file script. This wrapper forwards to the
new unified CLI implementation under the `dms/` package.
"""

from __future__ import annotations

from dms.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

