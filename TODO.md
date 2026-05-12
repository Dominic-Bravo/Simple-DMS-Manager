# TODO - DMS refactor (scalable/clean)

## Step 1: Create unified package structure
- Add `dms/` package with modules: `config.py`, `parsing.py`, `db.py`, `filesystem.py`, `export.py`, `pipeline.py`, `cli.py`, `__init__.py`.
- Ensure consistent SQLite schema: `document_records`.

## Step 2: Implement robust filename parsing
- Support both patterns:
  - `PR_2025-001.pdf`
  - `PR-2025-001.pdf`
- Validate doc type (PR/PO/DV/CAFOA/AIR/REC) and reference number.

## Step 3: Implement pipeline
- Scan inbox directory, copy/move into archive subfolder by doc type.
- Extract metadata (file size/date indexed/status).
- Validate records.
- Insert into SQLite using batched inserts.

## Step 4: Implement CLI
- `python -m dms.cli init-db`
- `python -m dms.cli index --dir <inbox>`
- Optional: `python -m dms.cli export --db <path>`

## Step 5: Backward compatibility wrappers
- Update `dms_manager.py` to forward to `dms.cli` (or pipeline) so existing usage still works.
- Update `codes/index.py` to thin wrapper that calls into the unified CLI/pipeline.

## Step 6: Documentation
- Update `README.md` with usage examples and supported filename formats.

## Step 7: Add tests
- Add `tests/test_parsing.py` and `tests/test_db.py`.

## Step 8: Smoke test
- Run CLI `init-db` and `index` with a sample directory.
- Run tests (if pytest is added).

