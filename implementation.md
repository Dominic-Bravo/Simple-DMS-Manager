# Implementation Guide

**Municipal Document Lifecycle Management System**
IT Intern Project — Municipal Government of Libungan

---

## Overview

This system automates the full document lifecycle for government records — from physical intake through categorization, metadata indexing, validation, and final migration into a SQL database. It was built to eliminate manual errors and streamline what was previously a paper-based process.

---

## Requirements

### Python version

Python 3.10 or higher is required. The program uses the built-in `match` syntax for type detection and relies on `str | None` union type hints.

To check your version:

```bash
python3 --version
```

### Dependencies

This project uses only Python standard library modules — no `pip install` is needed.

| Module | Purpose |
|--------|---------|
| `os` | File and path operations |
| `json` | Metadata serialization |
| `csv` | Exporting records to spreadsheet format |
| `sqlite3` | Local SQL database for migration testing |
| `shutil` | Copying files from inbox to archive |
| `datetime` | Timestamping indexed records |
| `pathlib` | Cross-platform path handling |

---

## Project structure

After first run, the program automatically creates this folder layout:

```
government_records/
├── inbox/              ← Drop raw scanned files here
├── archive/
│   ├── PR/             ← Purchase Requests
│   ├── PO/             ← Purchase Orders
│   ├── DV/             ← Disbursement Vouchers
│   ├── CAFOA/          ← Certificates of Availability of Funds
│   ├── AIR/            ← Acceptance and Inspection Reports
│   └── REC/            ← Receipts
├── export/             ← Generated CSV exports
└── records.db          ← SQLite database (auto-created)
```

You do not need to create these folders manually.

---

## Installation

### 1. Download the script

Save `document_manager.py` to a folder on your computer, for example:

```
C:\Users\YourName\Documents\DocManager\     (Windows)
/home/yourname/doc-manager/                 (Linux / Mac)
```

### 2. Verify Python is available

```bash
python3 document_manager.py --version
```

If Python is not recognized, download it from [python.org](https://www.python.org/downloads/) and ensure it is added to your system PATH during installation.

### 3. Run the program for the first time

```bash
cd /path/to/your/folder
python3 document_manager.py
```

On first run, the program will:

- Create the `government_records/` directory tree
- Generate sample demo files in the inbox to demonstrate the pipeline
- Process, validate, and export those demo records
- Create `records.db` (the local SQL database)

---

## Configuration

Open `document_manager.py` and locate the configuration section near the top:

```python
DOCUMENT_TYPES = {
    "PR":    "Purchase Request",
    "PO":    "Purchase Order",
    "DV":    "Disbursement Voucher",
    "CAFOA": "Certificate of Availability of Funds",
    "AIR":   "Acceptance and Inspection Report",
    "REC":   "Receipt",
}
```

To add a new document type, append a new key-value pair:

```python
"OR": "Official Receipt",
```

The new type will automatically get its own archive subfolder and be recognized during file processing.

### Changing the base directory

```python
BASE_DIR = Path("government_records")
```

Change `"government_records"` to any absolute or relative path where you want the system to store its data.

---

## Migrating to a real SQL database

The program uses SQLite by default, which stores data in a single `.db` file — ideal for development and testing. To migrate to a production database (PostgreSQL or MySQL), replace the `migrate_to_sql()` function body with the appropriate driver.

### PostgreSQL example

Install the driver first:

```bash
pip install psycopg2-binary
```

Then replace the connection line:

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="municipal_records",
    user="your_user",
    password="your_password"
)
```

The `INSERT` statement and table schema remain the same.

---

## Pipeline diagram

```
inbox/
  │
  ▼
detect_document_type()     ← categorize by filename prefix
  │
  ▼
extract_metadata()         ← build structured record
  │
  ▼
archive/[TYPE]/            ← copy file to correct folder
  │
  ▼
validate_records()         ← check for errors / empty files
  │
  ├── export/records.csv   ← spreadsheet export
  │
  └── records.db           ← SQL database insert
```

---

## Troubleshooting

**"Permission denied" error on Windows**
Run your terminal as Administrator, or move the project folder outside of `Program Files`.

**Files are skipped with `[SKIP] Unknown type`**
The filename does not start with a recognized document code. Rename the file to start with `PR-`, `PO-`, `DV-`, `CAFOA-`, `AIR-`, or `REC-` followed by a dash.

**"Empty file" validation warnings on demo run**
Expected — the demo creates zero-byte placeholder files. Real scanned documents will pass this check automatically.

**Database already exists / duplicate records**
The SQL table uses `INSERT` without a uniqueness check. If you re-run the pipeline on the same files, duplicates will be added. Add a `UNIQUE` constraint on `filename` in the `CREATE TABLE` statement and use `INSERT OR IGNORE` to prevent this.
