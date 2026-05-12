"""
Municipal Document Lifecycle Management System
IT Intern Project — Municipal Government of Libungan
Automates: organizing, categorizing, indexing, and preparing
government records for SQL database migration.
"""

import os
import json
import csv
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

DOCUMENT_TYPES = {
    "PR":    "Purchase Request",
    "PO":    "Purchase Order",
    "DV":    "Disbursement Voucher",
    "CAFOA": "Certificate of Availability of Funds",
    "AIR":   "Acceptance and Inspection Report",
    "REC":   "Receipt",
}

BASE_DIR     = Path("government_records")
INBOX_DIR    = BASE_DIR / "inbox"          # Drop raw files here
ARCHIVE_DIR  = BASE_DIR / "archive"        # Organized copies
EXPORT_DIR   = BASE_DIR / "export"         # CSV / SQL exports
DB_PATH      = BASE_DIR / "records.db"


# ─────────────────────────────────────────────
# STEP 1 — SETUP: create folder structure
# ─────────────────────────────────────────────

def setup_directories():
    """Create all required directories on first run."""
    for doc_type in DOCUMENT_TYPES:
        (ARCHIVE_DIR / doc_type).mkdir(parents=True, exist_ok=True)
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    print("[SETUP] Directory structure ready.")


# ─────────────────────────────────────────────
# STEP 2 — CATEGORIZE: detect document type
# ─────────────────────────────────────────────

def detect_document_type(filename: str) -> str | None:
    """
    Infer document type from filename prefix.
    E.g. 'PR-2025-001.pdf' → 'PR'
    """
    name = filename.upper()
    for code in DOCUMENT_TYPES:
        if name.startswith(code):
            return code
    return None


# ─────────────────────────────────────────────
# STEP 3 — INDEX: extract structured metadata
# ─────────────────────────────────────────────

def extract_metadata(filepath: Path, doc_type: str) -> dict:
    """
    Build a metadata record for a document.
    In production, you'd parse the actual file content here.
    """
    stat = filepath.stat()
    return {
        "filename":      filepath.name,
        "doc_type":      doc_type,
        "doc_type_full": DOCUMENT_TYPES[doc_type],
        "file_size_kb":  round(stat.st_size / 1024, 2),
        "date_indexed":  datetime.now().isoformat(),
        "status":        "indexed",
        "notes":         "",
    }


# ─────────────────────────────────────────────
# STEP 4 — AUTOMATE: process inbox
# ─────────────────────────────────────────────

def process_inbox() -> list[dict]:
    """
    Scan inbox, categorize each file, extract metadata,
    copy to the correct archive folder.
    Returns list of metadata records.
    """
    records = []
    files   = list(INBOX_DIR.iterdir())

    if not files:
        print("[INFO] Inbox is empty. Add files to:", INBOX_DIR)
        return records

    for filepath in files:
        if not filepath.is_file():
            continue

        doc_type = detect_document_type(filepath.name)

        if doc_type is None:
            print(f"  [SKIP] Unknown type: {filepath.name}")
            continue

        # Copy to archive subfolder
        dest = ARCHIVE_DIR / doc_type / filepath.name
        shutil.copy2(filepath, dest)

        # Build metadata
        meta = extract_metadata(filepath, doc_type)
        records.append(meta)
        print(f"  [OK]   {filepath.name}  →  {doc_type}/")

    print(f"\n[PROCESS] {len(records)} file(s) indexed.")
    return records


# ─────────────────────────────────────────────
# STEP 5 — VALIDATE: check data integrity
# ─────────────────────────────────────────────

def validate_records(records: list[dict]) -> list[dict]:
    """
    Validate required fields and flag any issues.
    """
    validated = []
    for rec in records:
        errors = []
        if not rec.get("filename"):
            errors.append("missing filename")
        if rec.get("doc_type") not in DOCUMENT_TYPES:
            errors.append("invalid doc_type")
        if rec.get("file_size_kb", 0) == 0:
            errors.append("empty file")

        rec["status"] = "error: " + "; ".join(errors) if errors else "validated"
        validated.append(rec)

    invalid = [r for r in validated if r["status"].startswith("error")]
    if invalid:
        print(f"[VALIDATE] ⚠ {len(invalid)} record(s) with issues:")
        for r in invalid:
            print(f"  {r['filename']}: {r['status']}")
    else:
        print(f"[VALIDATE] All {len(validated)} record(s) passed.")

    return validated


# ─────────────────────────────────────────────
# STEP 6 — EXPORT: save to CSV
# ─────────────────────────────────────────────

def export_to_csv(records: list[dict]):
    """Export indexed records to a CSV file for review."""
    if not records:
        return

    export_path = EXPORT_DIR / f"records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    fieldnames  = list(records[0].keys())

    with open(export_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"[EXPORT] CSV saved: {export_path}")


# ─────────────────────────────────────────────
# STEP 7 — SQL MIGRATION: load into SQLite
# ─────────────────────────────────────────────

def migrate_to_sql(records: list[dict]):
    """
    Insert validated records into a SQLite database —
    a local stand-in for the production SQL database.
    """
    if not records:
        return

    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            filename       TEXT NOT NULL,
            doc_type       TEXT NOT NULL,
            doc_type_full  TEXT,
            file_size_kb   REAL,
            date_indexed   TEXT,
            status         TEXT,
            notes          TEXT
        )
    """)

    for rec in records:
        cur.execute("""
            INSERT INTO documents
                (filename, doc_type, doc_type_full, file_size_kb,
                 date_indexed, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            rec["filename"], rec["doc_type"], rec["doc_type_full"],
            rec["file_size_kb"], rec["date_indexed"],
            rec["status"], rec["notes"],
        ))

    conn.commit()
    conn.close()
    print(f"[SQL] {len(records)} record(s) inserted into {DB_PATH}")


# ─────────────────────────────────────────────
# REPORT: summary by document type
# ─────────────────────────────────────────────

def print_summary(records: list[dict]):
    """Print a breakdown of processed documents by type."""
    if not records:
        return

    summary: dict[str, int] = {}
    for rec in records:
        summary[rec["doc_type"]] = summary.get(rec["doc_type"], 0) + 1

    print("\n" + "─" * 40)
    print("  DOCUMENT SUMMARY")
    print("─" * 40)
    for code, count in sorted(summary.items()):
        label = DOCUMENT_TYPES.get(code, code)
        print(f"  {code:<8} {label:<40} {count:>4} file(s)")
    print("─" * 40)
    print(f"  TOTAL   {'':40} {len(records):>4} file(s)")
    print("─" * 40 + "\n")


# ─────────────────────────────────────────────
# MAIN — full pipeline
# ─────────────────────────────────────────────

def main():
    print("\n══════════════════════════════════════════")
    print("  Municipal Document Management System")
    print("  Municipal Government of Libungan")
    print("══════════════════════════════════════════\n")

    # Step 1 — Setup
    setup_directories()

    # Demo: create sample files in inbox if empty
    sample_files = [
        "PR-2025-001.pdf", "PR-2025-002.pdf",
        "PO-2025-010.pdf",
        "DV-2025-005.pdf", "DV-2025-006.pdf",
        "CAFOA-2025-003.pdf",
        "AIR-2025-001.pdf",
        "REC-2025-007.pdf",
        "UNKNOWN-file.txt",   # intentional — tests skip logic
    ]
    for name in sample_files:
        (INBOX_DIR / name).touch()
    print(f"[DEMO] Created {len(sample_files)} sample files in inbox.\n")

    # Step 2–4 — Process inbox
    print("[STEP 4] Processing inbox...\n")
    records = process_inbox()

    # Step 5 — Validate
    print("\n[STEP 5] Validating records...")
    records = validate_records(records)

    # Step 6 — CSV export
    print("\n[STEP 6] Exporting to CSV...")
    export_to_csv(records)

    # Step 7 — SQL migration
    print("\n[STEP 7] Migrating to SQL database...")
    migrate_to_sql(records)

    # Report
    print_summary(records)
    print("Pipeline complete. ✓\n")


if __name__ == "__main__":
    main()