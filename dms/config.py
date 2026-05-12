from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_DOC_TYPES: dict[str, str] = {
    "PR": "Purchase Request",
    "PO": "Purchase Order",
    "DV": "Disbursement Voucher",
    "CAFOA": "Certificate of Availability of Funds",
    "AIR": "Acceptance and Inspection Report",
    "REC": "Receipt",
}


@dataclass(frozen=True)
class DMSConfig:
    """Runtime configuration.

    Keep this small and explicit so the project is easy to scale.
    """

    db_path: Path
    # Used when archiving/copying files.
    archive_root: Path
    # Document types allowed by the system.
    doc_types: dict[str, str]

    @property
    def allowed_doc_type_codes(self) -> set[str]:
        return set(self.doc_types.keys())


def default_config(project_root: Path) -> DMSConfig:
    base_dir = project_root / "government_records"
    return DMSConfig(
        db_path=base_dir / "records.db",
        archive_root=base_dir / "archive",
        doc_types=DEFAULT_DOC_TYPES,
    )

