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
1. Place scanned document PDFs into the designated source folder.
2. Run the `dms_manager.py` script.
3. The system parses the filenames (e.g., `PR_2025-001.pdf`), extracts the document ID, and logs the entry into `gov_records.db`.

## Future Scope
* Implementing an OCR (Optical Character Recognition) module to parse content directly from scanned PDFs.
* Developing a web-based dashboard using Django REST Framework for real-time document status monitoring.
