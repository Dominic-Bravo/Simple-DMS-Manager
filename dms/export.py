# dms/export.py

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from dms import config

def export_records_to_csv(records: List[Dict[str, Any]], export_dir: Path) -> Path | None:
    """
    Exports a list of document records to a timestamped CSV file.

    Args:
        records: A list of dictionaries, where each dictionary represents a record.
        export_dir: The directory where the CSV file should be saved.

    Returns:
        The Path object of the created CSV file, or None if no records were exported.
    """
    if not records:
        print("[EXPORT] No records to export to CSV.")
        return None

    # Ensure export directory exists
    export_dir.mkdir(parents=True, exist_ok=True)

    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"records_{timestamp}.csv"
    csv_path = export_dir / csv_filename

    # Define CSV headers based on expected record keys (matching DB columns)
    # Exclude 'doc_id' as it's an internal DB primary key
    fieldnames = [
        "doc_type", "reference_number", "filename", "date_filed",
        "date_indexed", "storage_location", "status", "file_size_kb", "notes"
    ]

    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in records:
                # Filter record to only include defined fieldnames
                filtered_record = {k: record.get(k) for k in fieldnames}
                writer.writerow(filtered_record)
        print(f"[EXPORT] CSV saved: {csv_path}")
        return csv_path
    except IOError as e:
        print(f"[EXPORT ERROR] Failed to write CSV file '{csv_path}': {e}")
        return None
