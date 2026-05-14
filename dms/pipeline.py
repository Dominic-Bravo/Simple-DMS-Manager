from pathlib import Path
from datetime import datetime

from dms import config
from dms import filesystem
from dms import parsing
from dms import db
from dms import export

def run_pipeline(inbox_dir: Path) -> dict:
    """
    Executes the document processing pipeline.

    This function orchestrates the following steps:
    1. Ensures the necessary directory structure for archiving and exports exists.
    2. Scans the specified inbox directory for files to process.
    3. For each file:
        a. Parses its filename to extract document type and reference number.
        b. Validates the parsed information.
        c. If valid, copies the file to its designated archive subfolder.
        d. Extracts additional metadata (file size, indexing date, etc.).
        e. Prepares a record for database insertion and CSV export.
        f. If parsing or archiving fails, records the error status.
    4. Inserts all successfully processed records into the SQLite database using
       batched inserts and an 'INSERT OR IGNORE' strategy to handle duplicates.
    5. Exports all attempted records (including those with errors) to a CSV file
       for comprehensive reporting.

    Args:
        inbox_dir (Path): The path to the directory containing new documents
                          to be processed.

    Returns:
        dict: A summary of the pipeline execution, containing counts of:
              - 'indexed': Number of files successfully parsed, archived, and
                           prepared for database insertion.
              - 'skipped_unknown_type': Number of files skipped due to an
                                        unrecognized document type in the filename.
              - 'skipped_invalid_format': Number of files skipped due to an
                                          invalid filename format or archiving failure.
    """
    indexed_count = 0
    skipped_unknown_type_count = 0
    skipped_invalid_format_count = 0
    records_for_db_insert = [] # Only successfully processed records for DB
    all_records_for_export = [] # All attempted records for CSV export

    print(f"[SETUP] Ensuring directory structure in {config.BASE_DIR}...")
    filesystem.ensure_directory_structure()
    print("[SETUP] Directory structure ready.")

    print(f"[STEP 1] Scanning inbox: {inbox_dir}...")
    files_in_inbox = filesystem.scan_directory(inbox_dir)
    print(f"[STEP 1] Found {len(files_in_inbox)} file(s) in inbox.")

    if not files_in_inbox:
        print("[PROCESS] No new files to process.")
        return {
            "indexed": indexed_count,
            "skipped_unknown_type": skipped_unknown_type_count,
            "skipped_invalid_format": skipped_invalid_format_count,
        }

    print("[STEP 2] Processing files...")
    for file_path in files_in_inbox:
        filename = file_path.name
        print(f"  Processing: {filename}")

        parsed_data = parsing.parse_filename(filename).to_record()
        doc_type = parsed_data["doc_type"]
        reference_number = parsed_data["reference_number"]
        is_valid_format = parsed_data["is_valid_format"]
        parsing_error_message = parsed_data["error"]

        current_timestamp = datetime.now()
        date_indexed_str = current_timestamp.isoformat()

        # Attempt to get file modification time for 'date_filed'
        date_filed_str = date_indexed_str # Default to indexed date
        file_size_kb = 0
        try:
            file_stat = file_path.stat()
            file_mod_timestamp = datetime.fromtimestamp(file_stat.st_mtime)
            date_filed_str = file_mod_timestamp.isoformat()
            file_size_kb = round(file_stat.st_size / 1024)
        except OSError as e:
            print(f"  [WARN] Could not get file stats for {filename}: {e}")
            # file_size_kb remains 0, date_filed_str remains date_indexed_str

        # Initialize record with common fields and default error status
        record = {
            "doc_type": doc_type, # Keep parsed doc_type even if format is invalid
            "reference_number": reference_number, # Keep parsed ref_num even if format is invalid
            "filename": filename,
            "date_filed": date_filed_str,
            "date_indexed": date_indexed_str,
            "storage_location": None,
            "status": "error: processing failed",
            "file_size_kb": file_size_kb,
            "notes": "",
        }

        if doc_type and reference_number and is_valid_format:
            # Document type recognized and filename format is valid
            try:
                # Copy file to its designated archive subfolder
                archive_path = filesystem.copy_file_to_archive(file_path, doc_type, filename)

                record.update({
                    "storage_location": str(archive_path),
                    "status": "validated",
                    "notes": "",
                })
                records_for_db_insert.append(record)
                indexed_count += 1
                print(f"  [OK]   {filename} -> {doc_type}/")
            except Exception as e:
                # Archiving failed, but parsing was successful
                record.update({
                    "status": f"error: archiving failed",
                    "notes": str(e),
                })
                skipped_invalid_format_count += 1
                print(f"  [FAIL] {filename} - Archiving failed: {e}")
        elif parsing_error_message and parsing_error_message.startswith("Unknown document type"):
            # Document type not recognized
            record.update({
                "doc_type": None, # Explicitly set to None if not recognized
                "reference_number": None, # Explicitly set to None if not recognized
                "status": "error: unknown document type",
                "notes": parsing_error_message if parsing_error_message else "Filename does not start with a recognized document type code.",
            })
            skipped_unknown_type_count += 1
            print(f"  [SKIP] Unknown type: {filename}")
        else:
            # Document type might be recognized, but filename format is invalid
            record.update({
                "status": "error: invalid filename format",
                "notes": parsing_error_message if parsing_error_message else "Filename format is incorrect.",
            })
            skipped_invalid_format_count += 1
            print(f"  [SKIP] Invalid format: {filename}")
        
        # Add the record to the list for CSV export, regardless of success or failure
        all_records_for_export.append(record)

    print(f"[STEP 2] Processed {len(files_in_inbox)} file(s).")

    print(f"[STEP 3] Inserting {len(records_for_db_insert)} record(s) into database...")
    if records_for_db_insert:
        db.init_db()
        inserted_count = db.insert_records(records_for_db_insert)
        ignored_count = len(records_for_db_insert) - inserted_count
        print(
            f"[STEP 3] {inserted_count} new record(s) inserted into {config.DB_NAME}; "
            f"{ignored_count} duplicate(s) ignored."
        )
    else:
        print("[STEP 3] No new valid records to insert into the database.")

    print("[STEP 4] Exporting records to CSV...")
    if all_records_for_export:
        export_dir = config.BASE_DIR / "export"
        export.export_records_to_csv(all_records_for_export, export_dir)
        print(f"[STEP 4] CSV export complete to {export_dir}.")
    else:
        print("[STEP 4] No records to export to CSV.")

    print("\n" + "-" * 40)
    print("  PIPELINE SUMMARY")
    print("-" * 40)
    print(f"  Indexed successfully: {indexed_count} file(s)")
    print(f"  Skipped (unknown type): {skipped_unknown_type_count} file(s)")
    print(f"  Skipped (invalid format/archiving failed): {skipped_invalid_format_count} file(s)")
    print("-" * 40)

    return {
        "indexed": indexed_count,
        "skipped_unknown_type": skipped_unknown_type_count,
        "skipped_invalid_format": skipped_invalid_format_count,
    }
