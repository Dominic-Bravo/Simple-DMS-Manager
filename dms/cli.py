# dms/cli.py

import argparse
import sys
from pathlib import Path

from dms import db, pipeline, config

def main():
    """
    Main entry point for the DMS command-line interface.
    Handles 'init-db' and 'index' commands.
    """
    parser = argparse.ArgumentParser(
        description="Municipal Document Management System CLI."
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init-db command
    init_db_parser = subparsers.add_parser(
        "init-db",
        help="Initialize the SQLite database and create necessary tables."
    )

    # index command
    index_parser = subparsers.add_parser(
        "index",
        help="Scan a directory, process documents, and index their metadata."
    )
    index_parser.add_argument(
        "--dir",
        type=str,
        default=str(config.BASE_DIR / config.INBOX_DIR_NAME),
        help=f"Path to the inbox directory containing documents to index. Defaults to '{config.BASE_DIR / config.INBOX_DIR_NAME}'."
    )

    args = parser.parse_args()

    if args.command == "init-db":
        print("[CLI] Initializing database...")
        db.init_db()
        print("[CLI] Database initialization complete.")
    elif args.command == "index":
        inbox_path = Path(args.dir)
        if not inbox_path.is_dir():
            print(f"[CLI ERROR] The specified inbox directory does not exist: {inbox_path}")
            sys.exit(1)
        print(f"[CLI] Starting document indexing for directory: {inbox_path}")
        summary = pipeline.run_pipeline(inbox_path)
        print(
            "\n[CLI SUMMARY] "
            f"Documents Indexed: {summary['indexed']} | "
            f"Skipped (Unknown Type): {summary['skipped_unknown_type']} | "
            f"Skipped (Invalid Format): {summary['skipped_invalid_format']}"
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
