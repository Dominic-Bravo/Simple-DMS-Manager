# User Guide

**Municipal Document Lifecycle Management System**
IT Intern Project — Municipal Government of Libungan

---

## What this system does

This program takes scanned government documents from an inbox folder, automatically sorts them by type (PR, PO, DV, etc.), records their metadata, checks for errors, and saves everything into a CSV report and a SQL database — replacing a manual, paper-based filing process.

---

## Quick start (3 steps)

### Step 1 — Run the program

Open a terminal in the folder where `document_manager.py` is saved and run:

```bash
python3 document_manager.py
```

The program will create the `government_records/` folder structure automatically on first run.

### Step 2 — Add your documents

Name each scanned file using the correct prefix and place it in the inbox:

```
government_records/inbox/
```

Naming format:

```
[TYPE]-[YEAR]-[NUMBER].pdf
```

Examples:

```
PR-2025-001.pdf
PO-2025-010.pdf
DV-2025-005.pdf
CAFOA-2025-003.pdf
AIR-2025-001.pdf
REC-2025-007.pdf
```

### Step 3 — Run the pipeline

```bash
python3 document_manager.py
```

The program will process every file in the inbox, sort it, validate it, and export the results.

---

## Document type codes

| Code | Full name |
|------|-----------|
| `PR` | Purchase Request |
| `PO` | Purchase Order |
| `DV` | Disbursement Voucher |
| `CAFOA` | Certificate of Availability of Funds |
| `AIR` | Acceptance and Inspection Report |
| `REC` | Receipt |

Files that do not start with one of these codes will be skipped with a `[SKIP]` message in the terminal. Rename the file to match the correct code before re-running.

---

## Reading the terminal output

When you run the program, you will see output like this:

```
[SETUP] Directory structure ready.

[STEP 4] Processing inbox...

  [OK]   PR-2025-001.pdf  →  PR/
  [OK]   PO-2025-010.pdf  →  PO/
  [SKIP] Unknown type: scan001.pdf

[PROCESS] 2 file(s) indexed.

[STEP 5] Validating records...
[VALIDATE] All 2 record(s) passed.

[STEP 6] Exporting to CSV...
[EXPORT] CSV saved: government_records/export/records_20250512_093000.csv

[STEP 7] Migrating to SQL database...
[SQL] 2 record(s) inserted into government_records/records.db

────────────────────────────────────────
  DOCUMENT SUMMARY
────────────────────────────────────────
  AIR      Acceptance and Inspection Report     1 file(s)
  PR       Purchase Request                     2 file(s)
  ...
────────────────────────────────────────
  TOTAL                                        8 file(s)
────────────────────────────────────────
```

| Message | Meaning |
|---------|---------|
| `[OK]` | File was recognized, archived, and indexed successfully |
| `[SKIP]` | File name was not recognized — needs renaming |
| `[VALIDATE] All passed` | No data errors found |
| `[VALIDATE] ⚠ issues` | One or more records have problems — see details below |
| `[EXPORT]` | CSV file was saved to the export folder |
| `[SQL]` | Records were inserted into the database |

---

## Finding your outputs

After each run, check these locations:

### Archived files

Sorted copies of your documents, organized by type:

```
government_records/archive/PR/
government_records/archive/PO/
government_records/archive/DV/
...
```

Original files in the inbox are not deleted — you can clear them manually after confirming the archive is correct.

### CSV export

A spreadsheet-ready file with all indexed records:

```
government_records/export/records_YYYYMMDD_HHMMSS.csv
```

Open this in Microsoft Excel or LibreOffice Calc. Each row contains:

| Column | Description |
|--------|-------------|
| `filename` | Original file name |
| `doc_type` | Short code (e.g. PR) |
| `doc_type_full` | Full document name |
| `file_size_kb` | File size in kilobytes |
| `date_indexed` | When it was processed |
| `status` | `validated` or `error: reason` |
| `notes` | Any additional notes |

### SQL database

```
government_records/records.db
```

Open this with any SQLite viewer (e.g. [DB Browser for SQLite](https://sqlitebrowser.org/), free download). The table is named `documents` and has the same columns as the CSV.

---

## Common tasks

### Process a batch of documents

1. Copy all scanned PDFs into `government_records/inbox/`
2. Ensure filenames start with the correct code (`PR-`, `PO-`, etc.)
3. Run `python3 document_manager.py`
4. Check the summary at the bottom of the terminal output
5. Open the CSV in Excel to review the indexed records

### Re-process a single file

Simply place the file back into the inbox and run the program again. Note that this will create a duplicate entry in the database — see the Implementation Guide for how to prevent duplicates.

### View all records in the database

Using DB Browser for SQLite:

1. Open `government_records/records.db`
2. Click the "Browse Data" tab
3. Select the `documents` table

Or use a quick SQL query:

```sql
SELECT * FROM documents WHERE doc_type = 'PR';
SELECT * FROM documents WHERE status LIKE 'error%';
SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type;
```

### Search for a specific document

```sql
SELECT * FROM documents WHERE filename LIKE '%2025-001%';
```

---

## Frequently asked questions

**What happens to my original files in the inbox?**
They are not moved or deleted. The program copies them to the archive folder. You can clear the inbox manually once you have confirmed the archive looks correct.

**Can I use formats other than PDF?**
Yes. The program detects document type from the filename prefix only, not the file content. Any file format (`.pdf`, `.jpg`, `.png`, `.docx`) will work as long as the filename starts with the correct code.

**What if two files have the same name?**
The second file will overwrite the first in the archive folder. Always use unique numbers in the filename (e.g. `PR-2025-001`, `PR-2025-002`) to avoid this.

**The program says "empty file" for my documents — why?**
This happens when the file size is 0 KB, which usually means the scan did not save correctly. Re-scan the document and replace the file in the inbox.

**Can multiple people use this at the same time?**
Not safely with SQLite — simultaneous writes can cause conflicts. For multi-user environments, migrate to PostgreSQL or MySQL (see the Implementation Guide).
