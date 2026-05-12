# Municipal Document Management System (DMS) — How to Use

This project indexes government documents (mostly PDFs) by **filename metadata**, archives the files by document type, and records metadata into a **SQLite** database.

## 1) What the system expects
### Supported filename patterns
The document type and reference number are extracted from the filename using this pattern (case-sensitive for the extension, case-insensitive for the doc type letters):

- `PR_2025-001.pdf`
- `PR-2025-001.pdf`

More generally:
- Document type: **2–5 uppercase letters** (e.g., `PR`, `PO`, `DV`, `CAFOA`, `AIR`, `REC`)
- Separator: `-` or `_`
- Reference number: `YYYY-N+` (example: `2025-001`)
- Extension: `.pdf`

### Allowed document type codes
Allowed codes are configured in `dms/config.py`:
- `PR` — Purchase Request
- `PO` — Purchase Order
- `DV` — Disbursement Voucher
- `CAFOA` — Certificate of Availability of Funds
- `AIR` — Acceptance and Inspection Report
- `REC` — Receipt

Files whose parsed `doc_type` is not in the allowed list are skipped.

## 2) Project folder layout (created automatically)
Default paths are defined by `dms/config.py` under `government_records/`:

- `government_records/inbox/`  — input files (you place files here)
- `government_records/archive/<DOC_TYPE>/` — archived copies by type
- `government_records/records.db` — SQLite database (auto-created on init)

> The archive subfolders for each allowed doc type are created automatically when indexing runs.

## 3) Prerequisites
- Python 3.10+ (tested patterns use modern Python typing)
- No external pip dependencies (standard library only)

Check Python:
```bash
python --version
```

## 4) Quick start
### Step A — Initialize the SQLite schema
Run:
```bash
python -m dms.cli init-db
```

This creates/initializes the SQLite database at:
- `government_records/records.db`

### Step B — Index documents in an inbox directory
Run:
```bash
python -m dms.cli index --dir government_records/inbox
```

What happens during indexing:
1. Scans the given directory for files ending in `.pdf`
2. Parses each filename into `(doc_type, reference_number)`
3. Archives a copy into `government_records/archive/<doc_type>/` (same filename preserved)
4. Inserts metadata into SQLite (`document_records` table)
5. Skips files that are not parseable or have unknown doc type

At the end you’ll see a summary like:
- `[OK] Indexed=<n> | Skipped(unknown)=<n> | Skipped(invalid)=<n>`

## 5) Where to find results
### Archived files
After indexing, look at:
- `government_records/archive/PR/`
- `government_records/archive/PO/`
- `government_records/archive/DV/`
- etc.

### SQLite database
Open:
- `government_records/records.db`

Table name:
- `document_records`

Columns (from schema):
- `doc_id` (primary key)
- `doc_type`
- `reference_number`
- `filename`
- `date_filed`
- `date_indexed`
- `storage_location`
- `status`
- `file_size_kb`
- `notes`

Duplicate handling:
- `UNIQUE(doc_type, reference_number)`
- inserts use `INSERT OR IGNORE`, so re-indexing the same doc type + reference won’t duplicate rows.

## 6) Adding new document types (code change)
If you want additional doc type codes, update `DEFAULT_DOC_TYPES` in `dms/config.py`.
Then rerun:
- `python -m dms.cli init-db`
- `python -m dms.cli index --dir <your-folder>`

> Note: you must also ensure filenames use the new code (e.g., `OR-2025-001.pdf`).

## 7) Backward-compatible entrypoints
These wrappers forward to the unified CLI:
- `dms_manager.py`
- `codes/index.py`

Typical usage:
```bash
python dms_manager.py init-db
python dms_manager.py index --dir government_records/inbox
```

(or similarly with `python codes/index.py ...`)

## 8) Troubleshooting
### “File skipped / invalid filename format” behavior
Common causes:
- Filename doesn’t match `TYPE_YYYY-N.pdf` or `TYPE-YYYY-N.pdf`
- Extension isn’t `.pdf`

### “Skipped(unknown)”
Cause:
- Parsed doc type is not in the allowed list in `dms/config.py`

### Nothing appears in the database
Check:
- You ran `init-db` first
- You passed the correct `--dir` containing `.pdf` files

---

## Notes about CSV export
`dms/export.py` contains `export_records_to_csv(records, export_dir)`, but the current CLI (`dms/cli.py`) exposes only:
- `init-db`
- `index --dir ...`

So CSV export is not currently a direct CLI command in this codebase.

