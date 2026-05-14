# dms/filesystem.py

import shutil
from pathlib import Path
from typing import List

from dms import config

def ensure_directory_structure() -> None:
    """
    Ensures the base directory, inbox, archive, export, and document type
    archive subdirectories exist.
    """
    # Create base directory
    config.BASE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[FS] Base directory ensured: {config.BASE_DIR}")

    # Create inbox directory
    inbox_path = config.BASE_DIR / config.INBOX_DIR_NAME
    inbox_path.mkdir(exist_ok=True)
    print(f"[FS] Inbox directory ensured: {inbox_path}")

    # Create export directory
    export_path = config.BASE_DIR / config.EXPORT_DIR_NAME
    export_path.mkdir(exist_ok=True)
    print(f"[FS] Export directory ensured: {export_path}")

    # Create archive directory and subdirectories for each document type
    archive_base_path = config.BASE_DIR / config.ARCHIVE_DIR_NAME
    archive_base_path.mkdir(exist_ok=True)
    print(f"[FS] Archive base directory ensured: {archive_base_path}")

    for doc_type in config.DEFAULT_DOC_TYPES.keys():
        doc_type_archive_path = archive_base_path / doc_type
        doc_type_archive_path.mkdir(exist_ok=True)
        print(f"[FS] Archive subdirectory ensured: {doc_type_archive_path}")

def scan_directory(path: Path) -> List[Path]:
    """
    Scans a given directory for files ending with '.pdf' (case-insensitive).

    Args:
        path: The Path object representing the directory to scan.

    Returns:
        A list of Path objects for all found PDF files.
    """
    if not path.is_dir():
        print(f"[FS ERROR] Directory not found: {path}")
        return []

    pdf_files: List[Path] = []
    for item in path.iterdir():
        if item.is_file() and item.suffix.lower() == '.pdf':
            pdf_files.append(item)
    return pdf_files

def copy_file_to_archive(source_path: Path, doc_type: str, filename: str) -> Path:
    """
    Copies a file from its source path to the appropriate archive subdirectory.

    Args:
        source_path: The original path of the file.
        doc_type: The document type (e.g., 'PR') which determines the archive subfolder.
        filename: The name of the file (used for the destination filename).

    Returns:
        The Path object of the newly copied file in the archive.
    """
    archive_doc_type_path = config.BASE_DIR / config.ARCHIVE_DIR_NAME / doc_type
    destination_path = archive_doc_type_path / filename

    try:
        shutil.copy2(source_path, destination_path) # copy2 preserves metadata
        print(f"[FS] Copied '{source_path.name}' to '{destination_path}'")
        return destination_path
    except FileNotFoundError:
        print(f"[FS ERROR] Source file not found: {source_path}")
        raise
    except Exception as e:
        print(f"[FS ERROR] Failed to copy file '{source_path.name}' to '{destination_path}': {e}")
        raise
