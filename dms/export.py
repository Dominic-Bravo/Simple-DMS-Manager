from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path


def export_records_to_csv(records: list[dict], export_dir: Path) -> Path | None:
    """Export indexed records to CSV for review."""
    if not records:
        return None

    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    fieldnames = list(records[0].keys())
    with open(export_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return export_path

