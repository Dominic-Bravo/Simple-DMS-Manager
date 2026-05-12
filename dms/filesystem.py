from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileMoveResult:
    original_path: Path
    archived_path: Path


def ensure_archive_structure(archive_root: Path, doc_type_codes: set[str]) -> None:
    for code in doc_type_codes:
        (archive_root / code).mkdir(parents=True, exist_ok=True)


def archive_file(src: Path, archive_root: Path, doc_type: str) -> FileMoveResult:
    """Copy the file into archive_root/<doc_type>/ preserving filename."""
    dest_dir = archive_root / doc_type
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / src.name
    shutil.copy2(src, dest_path)
    return FileMoveResult(original_path=src, archived_path=dest_path)


