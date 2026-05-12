from __future__ import annotations

import argparse
from pathlib import Path

from .config import default_config
from .db import connect, init_db
from .export import export_records_to_csv
from .pipeline import index_directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dms", description="Municipal DMS - document indexing")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init-db", help="Initialize SQLite schema")

    p_index = sub.add_parser("index", help="Index documents in a directory")
    p_index.add_argument("--dir", dest="directory", required=True, help="Directory containing PDFs")

    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parents[1]
    config = default_config(project_root)

    if args.cmd == "init-db":
        init_db(config.db_path)
        print(f"[OK] DB initialized: {config.db_path}")
        return 0

    if args.cmd == "index":
        directory_path = Path(args.directory)
        conn = connect(config.db_path)
        try:
            result = index_directory(directory_path=directory_path, config=config, conn=conn)
        finally:
            conn.close()

        print(
            f"[OK] Indexed={result.indexed} | Skipped(unknown)={result.skipped_unknown} | Skipped(invalid)={result.skipped_invalid}"
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

