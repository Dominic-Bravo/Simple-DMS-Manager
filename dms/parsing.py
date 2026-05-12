from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedFilename:
    doc_type: str
    reference_number: str


# Matches either:
# - PR_2025-001.pdf
# - PR-2025-001.pdf
_FILENAME_RE = re.compile(
    r"^(?P<doc_type>[A-Z]{2,5})[-_](?P<ref>\d{4}-\d+)(?:\.[Pp][Dd][Ff])$"
)


def parse_filename(filename: str) -> ParsedFilename:
    """Parse a document filename into structured data.

    Expected patterns (case-insensitive for doc_type, extension):
    - PR_2025-001.pdf
    - PR-2025-001.pdf

    Raises:
        ValueError: if the filename doesn't match the expected format.
    """
    fname = filename.strip()
    m = _FILENAME_RE.match(fname)
    if not m:
        raise ValueError(
            "Invalid filename format. Expected e.g. PR_2025-001.pdf or PR-2025-001.pdf"
        )

    doc_type = m.group("doc_type").upper()
    reference_number = m.group("ref")
    return ParsedFilename(doc_type=doc_type, reference_number=reference_number)

