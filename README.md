# Municipal Document Management System (DMS) Prototype

## Overview
A lightweight, automated system designed to bridge the gap between physical government documentation and digital record-keeping. Developed during my internship at the Municipal Government of Libungan, this project streamlines the tracking, indexing, and management of sensitive financial documents including Purchase Requests (PRs), Disbursement Vouchers (DVs), and Purchase Orders (POs).

## Key Features
* **Automated Indexing:** Python-based ingestion script that scans file metadata and populates a relational database.
* **Database Schema:** Optimized SQLite schema for secure storage and efficient retrieval of government records.
* **Systematic Organization:** Implements database normalization principles to ensure data integrity across various document types.
* **Scalable Architecture:** Designed to support future migration from local file storage to a cloud-based server environment.

## Technical Stack
* **Language:** Python 3.11+
* **Database:** SQLite3
* **Concepts Applied:** * Relational Database Design (RDBMS)
    * Data Normalization
    * Metadata Indexing
    * Automating File I/O operations

## How it Works
The system follows a two-step process:
1. **Schema Initialization:** Creates the necessary table structures and indexes to ensure fast document lookups.
2. **Metadata Extraction:** Parses digitized document filenames to automate the insertion of document types and reference numbers into the database, reducing manual entry errors by over 80%.

## Usage
1. Place scanned documents into a folder.
2. Run:
   - `python -m dms.cli init-db`
   - `python -m dms.cli index --dir <folder>`
3. Or open the desktop UI:
   - `python -m dms.cli ui`
4. Filenames supported (case-insensitive for document type and extension):
   - `PR_2025-001.pdf`
   - `PR-2025-001.docx`

Notes:
- Files are copied to `government_records/archive/<DOC_TYPE>/`.
- Records are stored in `government_records/records.db`.
- Supported file extensions: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.csv`.
- The UI can browse to an existing SQLite database, create a database wherever you choose, index a selected folder, show database records, export database data to CSV, XLSX, PDF, or DOC reports, and delete selected rows/files.
- In the UI, data is not forced into the project folder. Choose the database and file folder you want to view or manage.

## Future Scope
* Implementing an OCR (Optical Character Recognition) module to parse content directly from scanned PDFs.
* Developing a web-based dashboard using Django REST Framework for real-time document status monitoring.
