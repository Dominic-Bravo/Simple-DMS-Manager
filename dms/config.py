from pathlib import Path

# Base directory for all government records.
# All relative paths for inbox, archive, and database will be resolved against this.
BASE_DIR = Path("government_records")

# Default document types supported by the system.
# These are used for validation during filename parsing and for creating archive subdirectories.
DEFAULT_DOC_TYPES = {
    "PR",  # Purchase Request
    "PO",  # Purchase Order
    "DV",  # Disbursement Voucher
    "CAFOA", # Certificate of Availability of Funds
    "AIR", # Acceptance and Inspection Report
    "REC"  # Receipt
}

# Database configuration.
# Name of the SQLite database file.
DB_NAME = "records.db"
# Name of the table within the database where document records are stored.
DB_TABLE_NAME = "document_records"
