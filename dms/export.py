# dms/export.py

import csv
import html
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from xml.sax.saxutils import escape

from dms import config

FIELDNAMES = [
    "doc_id", "doc_type", "reference_number", "filename", "date_filed",
    "date_indexed", "storage_location", "status", "file_size_kb", "notes"
]

def _timestamped_path(export_dir: Path, suffix: str) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return export_dir / f"records_{timestamp}.{suffix}"

def _rows_with_headers(records: List[Dict[str, Any]]) -> list[list[Any]]:
    return [FIELDNAMES] + [[record.get(field, "") for field in FIELDNAMES] for record in records]

def export_records_to_csv(records: List[Dict[str, Any]], export_dir: Path) -> Path | None:
    """
    Exports a list of document records to a timestamped CSV file.

    Args:
        records: A list of dictionaries, where each dictionary represents a record.
        export_dir: The directory where the CSV file should be saved.

    Returns:
        The Path object of the created CSV file, or None if no records were exported.
    """
    if not records:
        print("[EXPORT] No records to export to CSV.")
        return None

    csv_path = _timestamped_path(export_dir, "csv")

    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
            writer.writeheader()
            for record in records:
                # Filter record to only include defined fieldnames
                filtered_record = {k: record.get(k) for k in FIELDNAMES}
                writer.writerow(filtered_record)
        print(f"[EXPORT] CSV saved: {csv_path}")
        return csv_path
    except IOError as e:
        print(f"[EXPORT ERROR] Failed to write CSV file '{csv_path}': {e}")
        return None

def export_records_to_html(records: List[Dict[str, Any]], export_dir: Path) -> Path | None:
    """Exports records to a printable HTML report."""
    if not records:
        print("[EXPORT] No records to export to HTML.")
        return None

    html_path = _timestamped_path(export_dir, "html")
    table_rows = []
    for row in _rows_with_headers(records):
        tag = "th" if row == FIELDNAMES else "td"
        cells = "".join(f"<{tag}>{html.escape(str(value or ''))}</{tag}>" for value in row)
        table_rows.append(f"<tr>{cells}</tr>")

    content = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Document Records Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
    h1 {{ font-size: 22px; margin-bottom: 4px; }}
    p {{ color: #555; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px; text-align: left; vertical-align: top; }}
    th {{ background: #f2f2f2; }}
  </style>
</head>
<body>
  <h1>Document Records Report</h1>
  <p>Generated {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
  <table>
    {''.join(table_rows)}
  </table>
</body>
</html>
"""
    try:
        html_path.write_text(content, encoding="utf-8")
        print(f"[EXPORT] HTML saved: {html_path}")
        return html_path
    except IOError as e:
        print(f"[EXPORT ERROR] Failed to write HTML file '{html_path}': {e}")
        return None

def export_records_to_doc(records: List[Dict[str, Any]], export_dir: Path) -> Path | None:
    """Exports records to a Word-compatible .doc file containing HTML."""
    html_path = export_records_to_html(records, export_dir)
    if not html_path:
        return None
    doc_path = html_path.with_suffix(".doc")
    try:
        html_path.replace(doc_path)
        print(f"[EXPORT] DOC saved: {doc_path}")
        return doc_path
    except IOError as e:
        print(f"[EXPORT ERROR] Failed to write DOC file '{doc_path}': {e}")
        return None

def export_records_to_xlsx(records: List[Dict[str, Any]], export_dir: Path) -> Path | None:
    """Exports records to a basic XLSX workbook using only the Python standard library."""
    if not records:
        print("[EXPORT] No records to export to XLSX.")
        return None

    xlsx_path = _timestamped_path(export_dir, "xlsx")
    rows = _rows_with_headers(records)

    sheet_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            col_name = _excel_column_name(col_index)
            value_text = escape(str(value or ""))
            cells.append(
                f'<c r="{col_name}{row_index}" t="inlineStr">'
                f"<is><t>{value_text}</t></is></c>"
            )
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData>'
        '</worksheet>'
    )

    try:
        with zipfile.ZipFile(xlsx_path, "w", zipfile.ZIP_DEFLATED) as workbook:
            workbook.writestr("[Content_Types].xml", _xlsx_content_types())
            workbook.writestr("_rels/.rels", _xlsx_root_rels())
            workbook.writestr("xl/workbook.xml", _xlsx_workbook())
            workbook.writestr("xl/_rels/workbook.xml.rels", _xlsx_workbook_rels())
            workbook.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        print(f"[EXPORT] XLSX saved: {xlsx_path}")
        return xlsx_path
    except IOError as e:
        print(f"[EXPORT ERROR] Failed to write XLSX file '{xlsx_path}': {e}")
        return None

def export_records_to_pdf(records: List[Dict[str, Any]], export_dir: Path) -> Path | None:
    """Exports records to a simple text-based PDF report."""
    if not records:
        print("[EXPORT] No records to export to PDF.")
        return None

    pdf_path = _timestamped_path(export_dir, "pdf")
    lines = ["Document Records Report", f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
    for record in records:
        lines.append(
            f"{record.get('doc_id', '')}. {record.get('doc_type', '')} "
            f"{record.get('reference_number', '')} - {record.get('filename', '')}"
        )
        lines.append(f"   Status: {record.get('status', '')}")
        lines.append(f"   Location: {record.get('storage_location', '')}")
        lines.append("")

    try:
        pdf_path.write_bytes(_build_simple_pdf(lines))
        print(f"[EXPORT] PDF saved: {pdf_path}")
        return pdf_path
    except IOError as e:
        print(f"[EXPORT ERROR] Failed to write PDF file '{pdf_path}': {e}")
        return None

def _excel_column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name

def _xlsx_content_types() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""

def _xlsx_root_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

def _xlsx_workbook() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Document Records" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

def _xlsx_workbook_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

def _build_simple_pdf(lines: list[str]) -> bytes:
    safe_lines = [_pdf_escape(line) for line in lines[:45]]
    text_ops = ["BT", "/F1 11 Tf", "50 780 Td"]
    for index, line in enumerate(safe_lines):
        if index:
            text_ops.append("0 -16 Td")
        text_ops.append(f"({line}) Tj")
    text_ops.append("ET")
    stream = "\n".join(text_ops).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)

def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
