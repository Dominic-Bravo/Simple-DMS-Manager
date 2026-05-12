from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import sqlite3

from .config import DMSConfig
from .db import insert_records
from .filesystem import archive_file, ensure_archive_structure
from .parsing import parse_filename


@dataclass
class IndexResult:
    indexed: int
    skipped_unknown: int
    skipped_invalid: int


def build_record(
    *,
    filename: str,
    doc_type: str,
    reference_number: str,
    archived_path: Path,
    file_size_kb: float,
) -> dict:
    return {
        "doc_type": doc_type,
        "reference_number": reference_number,
        "filename": filename,
        "date_indexed": datetime.now().isoformat(),
        "storage_location": str(archived_path.parent),
        "status": "validated",
        "file_size_kb": file_size_kb,
        "notes": "",
    }


def validate_record(record: dict) -> tuple[bool, str | None]:
    if record.get("doc_type") is None:
        return False, "missing doc_type"
    if not record.get("reference_number"):
        return False, "missing reference_number"
    if not record.get("filename"):
        return False, "missing filename"
    return True, None


def index_directory(
    *,
    directory_path: Path,
    config: DMSConfig,
    conn: sqlite3.Connection,
) -> IndexResult:
    ensure_archive_structure(config.archive_root, config.allowed_doc_type_codes)

    indexed_records: list[dict] = []
    skipped_unknown = 0
    skipped_invalid = 0

    if not directory_path.exists():
        raise FileNotFoundError(str(directory_path))

    for p in directory_path.iterdir():
        if not p.is_file() or p.suffix.lower() != ".pdf":
            continue

        try:
            parsed = parse_filename(p.name)
        except ValueError:
            skipped_invalid += 1
            continue

        if parsed.doc_type not in config.allowed_doc_type_codes:
            skipped_unknown += 1
            continue

        archived = archive_file(p, config.archive_root, parsed.doc_type)

        file_size_kb = round(p.stat().st_size / 1024, 2)
        rec = build_record(
            filename=p.name,
            doc_type=parsed.doc_type,
            reference_number=parsed.reference_number,
            archived_path=archived.archived_path,
            file_size_kb=file_size_kb,
        )

        ok, _reason = validate_record(rec)
        if ok:
            indexed_records.append(rec)

    insert_records(conn, indexed_records)

    return IndexResult(
        indexed=len(indexed_records),
        skipped_unknown=skipped_unknown,
        skipped_invalid=skipped_invalid,
    )

