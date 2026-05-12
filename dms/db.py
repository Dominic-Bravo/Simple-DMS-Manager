from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS document_records (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_type TEXT NOT NULL,
    reference_number TEXT NOT NULL,
    filename TEXT NOT NULL,

    date_filed DATE DEFAULT CURRENT_DATE,
    date_indexed TEXT,

    storage_location TEXT,
    status TEXT DEFAULT 'Archived',

    file_size_kb REAL,
    notes TEXT,

    UNIQUE(doc_type, reference_number)
);

CREATE INDEX IF NOT EXISTS idx_doc_type ON document_records(doc_type);
CREATE INDEX IF NOT EXISTS idx_reference_number ON document_records(reference_number);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


def insert_records(
    conn: sqlite3.Connection,
    records: list[dict],
) -> None:
    """Insert records in a single transaction.

    Uses INSERT OR IGNORE to avoid crashing on duplicates.
    """

    if not records:
        return

    cur = conn.cursor()
    cur.executemany(
        """
        INSERT OR IGNORE INTO document_records
            (doc_type, reference_number, filename, date_indexed, storage_location, status, file_size_kb, notes)
        VALUES
            (?, ?, ?, ?, ?, ?, ?, ?)
        """,

        [
            (
                r["doc_type"],
                r["reference_number"],
                r["filename"],
                r.get("date_indexed"),
                r.get("storage_location"),
                r.get("status"),
                r.get("file_size_kb"),
                r.get("notes"),
            )
            for r in records
        ],
    )
    conn.commit()


