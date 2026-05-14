# dms/db.py

import sqlite3
from pathlib import Path
from typing import List, Dict, Any

from dms import config

_db_path_override: Path | None = None

RECORD_COLUMNS = [
    "doc_id", "doc_type", "reference_number", "filename", "date_filed",
    "date_indexed", "storage_location", "status", "file_size_kb", "notes"
]

def get_db_path() -> Path:
    """Returns the full path to the SQLite database file."""
    if _db_path_override is not None:
        return _db_path_override
    return config.BASE_DIR / config.DB_NAME

def set_db_path(path: Path | str | None) -> None:
    """Overrides the active SQLite database path for UI/viewer workflows."""
    global _db_path_override
    _db_path_override = Path(path) if path else None

def init_db() -> None:
    """
    Initializes the SQLite database and creates the document_records table
    if it does not already exist.
    Ensures a unique constraint on (doc_type, reference_number).
    """
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True) # Ensure parent directory exists

    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # SQL to create the document_records table
        # doc_id: Primary Key, auto-incrementing integer
        # doc_type: The short code for the document type (e.g., PR, PO)
        # reference_number: The unique identifier for the document (e.g., 2025-001)
        # filename: The original filename
        # date_filed: The date the document was officially filed (can be extracted later or left null)
        # date_indexed: The timestamp when the document was processed by the system
        # storage_location: The path to the archived file
        # status: Current status (e.g., 'validated', 'error: reason')
        # file_size_kb: Size of the file in kilobytes
        # notes: Any additional notes
        # UNIQUE(doc_type, reference_number): Ensures no duplicate records for the same document type and reference number.
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {config.DB_TABLE_NAME} (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_type TEXT NOT NULL,
            reference_number TEXT NOT NULL,
            filename TEXT NOT NULL,
            date_filed TEXT,
            date_indexed TEXT NOT NULL,
            storage_location TEXT NOT NULL,
            status TEXT NOT NULL,
            file_size_kb INTEGER NOT NULL,
            notes TEXT,
            UNIQUE(doc_type, reference_number)
        );
        """
        cursor.execute(create_table_sql)
        conn.commit()
        print(f"[DB] Database initialized: {db_path}")
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to initialize database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def insert_records(records: List[Dict[str, Any]]) -> int:
    """
    Inserts a list of document records into the database.
    Uses INSERT OR IGNORE to prevent adding duplicate records based on the
    UNIQUE constraint (doc_type, reference_number).

    Args:
        records: A list of dictionaries, where each dictionary represents a record
                 with keys matching the database columns.

    Returns:
        The number of records successfully inserted.
    """
    if not records:
        return 0

    db_path = get_db_path()
    conn: sqlite3.Connection | None = None
    inserted_count = 0
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Prepare the INSERT OR IGNORE statement
        columns = [
            "doc_type", "reference_number", "filename", "date_filed",
            "date_indexed", "storage_location", "status", "file_size_kb", "notes"
        ]
        placeholders = ", ".join(["?"] * len(columns))
        insert_sql = f"""
        INSERT OR IGNORE INTO {config.DB_TABLE_NAME} ({", ".join(columns)})
        VALUES ({placeholders});
        """

        # Prepare data for executemany
        data_to_insert = []
        for record in records:
            data_to_insert.append(tuple(record.get(col) for col in columns))

        cursor.executemany(insert_sql, data_to_insert)
        conn.commit()

        # Count actual inserts by checking changes since last commit
        # This is a bit tricky with INSERT OR IGNORE, as changes might not reflect ignored rows.
        # A more robust way would be to query for existing records before inserting,
        # but for simplicity and performance, we'll rely on the DB's change count.
        # Note: lastrowid is for single inserts, rowcount for executemany.
        # rowcount gives total rows affected, which includes inserts.
        inserted_count = cursor.rowcount
        print(f"[DB] {inserted_count} record(s) processed for insertion.")

    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to insert records: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    return inserted_count

def fetch_records() -> List[Dict[str, Any]]:
    """Returns all document records ordered by newest indexed date first."""
    db_path = get_db_path()
    if not db_path.exists():
        return []

    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {", ".join(RECORD_COLUMNS)}
            FROM {config.DB_TABLE_NAME}
            ORDER BY date_indexed DESC, doc_id DESC;
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to fetch records: {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_record(doc_id: int) -> bool:
    """Deletes a document record by primary key."""
    db_path = get_db_path()
    if not db_path.exists():
        return False

    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM {config.DB_TABLE_NAME} WHERE doc_id = ?;",
            (doc_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"[DB ERROR] Failed to delete record: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
