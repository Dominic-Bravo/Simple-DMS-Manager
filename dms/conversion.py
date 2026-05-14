import csv
import html
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from dms import export

OUTPUT_FORMATS = {
    "CSV": ".csv",
    "Excel": ".xlsx",
    "PDF": ".pdf",
    "DOC": ".doc",
    "HTML": ".html",
    "Text": ".txt",
}


def convert_file(source_path: Path, output_path: Path) -> Path:
    """Converts a selected file into a simple viewable report format."""
    source_path = Path(source_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if source_path.suffix.lower() == output_path.suffix.lower():
        shutil.copy2(source_path, output_path)
        return output_path

    details = _file_details(source_path)
    suffix = output_path.suffix.lower()

    if suffix == ".csv":
        _write_csv(details, output_path)
    elif suffix == ".xlsx":
        _write_xlsx(details, output_path)
    elif suffix == ".pdf":
        lines = ["File Conversion Report", ""]
        lines.extend(f"{key}: {value}" for key, value in details)
        output_path.write_bytes(export._build_simple_pdf(lines))
    elif suffix == ".doc":
        _write_html(details, output_path)
    elif suffix == ".html":
        _write_html(details, output_path)
    elif suffix == ".txt":
        output_path.write_text(
            "\n".join(f"{key}: {value}" for key, value in details),
            encoding="utf-8",
        )
    else:
        raise ValueError(f"Unsupported output format: {suffix}")

    return output_path


def _file_details(source_path: Path) -> list[tuple[str, str]]:
    stat = source_path.stat()
    details = [
        ("Source file", str(source_path)),
        ("Original name", source_path.name),
        ("Original extension", source_path.suffix or "(none)"),
        ("File size bytes", str(stat.st_size)),
        ("Modified", datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")),
        ("Converted", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    ]

    preview = _read_text_preview(source_path)
    if preview:
        details.append(("Text preview", preview))
    else:
        details.append((
            "Text preview",
            "Binary file content was not extracted. This output is a viewable file report.",
        ))
    return details


def _read_text_preview(source_path: Path) -> str:
    if source_path.suffix.lower() not in {".csv", ".txt", ".html"}:
        return ""
    try:
        text = source_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[:2000]


def _write_csv(details: list[tuple[str, str]], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["field", "value"])
        writer.writerows(details)


def _write_html(details: list[tuple[str, str]], output_path: Path) -> None:
    rows = "".join(
        "<tr>"
        f"<th>{html.escape(key)}</th>"
        f"<td>{html.escape(value)}</td>"
        "</tr>"
        for key, value in details
    )
    content = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>File Conversion Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; }}
    h1 {{ font-size: 22px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ width: 180px; background: #f2f2f2; }}
  </style>
</head>
<body>
  <h1>File Conversion Report</h1>
  <table>{rows}</table>
</body>
</html>
"""
    output_path.write_text(content, encoding="utf-8")


def _write_xlsx(details: list[tuple[str, str]], output_path: Path) -> None:
    rows = [["field", "value"], *details]
    sheet_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            col_name = export._excel_column_name(col_index)
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

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", export._xlsx_content_types())
        workbook.writestr("_rels/.rels", export._xlsx_root_rels())
        workbook.writestr("xl/workbook.xml", export._xlsx_workbook())
        workbook.writestr("xl/_rels/workbook.xml.rels", export._xlsx_workbook_rels())
        workbook.writestr("xl/worksheets/sheet1.xml", sheet_xml)
