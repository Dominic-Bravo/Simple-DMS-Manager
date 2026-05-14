import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dms.config import DEFAULT_DOC_TYPES

@dataclass
class ParsedFilename:
    """
    A dataclass to hold the results of filename parsing.

    Attributes:
        original_filename (str): The original filename that was parsed.
        doc_type (Optional[str]): The extracted document type (e.g., "PR", "PO").
                                   None if parsing failed or type is unknown.
        reference_number (Optional[str]): The extracted reference number (e.g., "2025-001").
                                          None if parsing failed.
        status (str): The status of the parsing operation. Can be "success", "error", or "skipped".
        error_message (Optional[str]): A message detailing any error or reason for skipping.
    """
    original_filename: str
    doc_type: Optional[str] = None
    reference_number: Optional[str] = None
    status: str = "error"  # Default status is error, updated on success or specific skip conditions
    error_message: Optional[str] = None

    @property
    def is_valid_format(self) -> bool:
        return self.status == "success"

    def to_record(self) -> dict[str, Optional[str] | bool]:
        return {
            "doc_type": self.doc_type,
            "reference_number": self.reference_number,
            "is_valid_format": self.is_valid_format,
            "error": self.error_message,
        }

def parse_filename(filename: str) -> ParsedFilename:
    """
    Parses a filename to extract the document type and reference number.

    This function supports two filename patterns:
    1. `TYPE_YYYY-N.pdf` (e.g., "PR_2025-001.pdf")
    2. `TYPE-YYYY-N.pdf` (e.g., "PR-2025-001.pdf")

    The document type and `.pdf` extension are case-insensitive for matching.

    Args:
        filename (str): The name of the file to parse.

    Returns:
        ParsedFilename: A dataclass containing the parsed data, status, and any error message.
    """
    # 1. Validate the file extension.
    if Path(filename).suffix.lower() != ".pdf":
        return ParsedFilename(
            original_filename=filename,
            status="skipped",
            error_message="File does not have a '.pdf' extension."
        )

    # Remove the '.pdf' extension to parse the core filename
    name_without_ext = Path(filename).stem

    # 2. Use a regular expression to extract document type and reference number.
    # The regex captures:
    #   - Group 1: Document Type (e.g., "PR", "PO") - one or more letters.
    #   - Separator: Either '_' or '-' between type and reference number.
    #   - Group 2: Reference Number (e.g., "2025-001") - four digits, a hyphen, then one or more digits.
    # The `^` and `$` anchors ensure the entire string matches the pattern.
    pattern = re.compile(r"^([A-Za-z]+)[_-](\d{4}-\d+)$")
    match = pattern.match(name_without_ext)

    if not match:
        return ParsedFilename(
            original_filename=filename,
            status="skipped",
            error_message="Filename does not match expected pattern (e.g., 'TYPE_YYYY-N.pdf' or 'TYPE-YYYY-N.pdf')."
        )

    extracted_doc_type, extracted_ref_number = match.groups()
    # Convert the extracted document type to uppercase for consistent validation
    extracted_doc_type_upper = extracted_doc_type.upper()

    # 3. Validate the extracted document type against the list of known types.
    if extracted_doc_type_upper not in DEFAULT_DOC_TYPES:
        return ParsedFilename(
            original_filename=filename,
            status="skipped",
            error_message=f"Unknown document type '{extracted_doc_type}'. Expected one of: {', '.join(sorted(DEFAULT_DOC_TYPES))}."
        )

    # 4. The reference number format (YYYY-N+) is implicitly validated by the regex `\d{4}-\d+`.
    # No further explicit validation is needed for the reference number itself.

    # If all checks pass, return a success status with the parsed data.
    return ParsedFilename(
        original_filename=filename,
        doc_type=extracted_doc_type_upper,
        reference_number=extracted_ref_number,
        status="success",
        error_message=None
    )
