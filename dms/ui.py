import contextlib
import io
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dms import config, conversion, db, export, filesystem, pipeline


class DmsApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Municipal Document Management System")
        self.geometry("1180x720")
        self.minsize(960, 620)

        default_db = Path.home() / "Documents" / config.DB_NAME
        self.db_path = tk.StringVar(value=str(default_db))
        self.inbox_dir = tk.StringVar(value="")
        self.status_text = tk.StringVar(value="Ready")
        self.records = []
        self.folder_files = []

        self._build_layout()
        self._set_active_database(default_db)
        self.refresh_records()
        self.refresh_files()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        toolbar = ttk.Frame(self, padding=10)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(1, weight=1)

        ttk.Label(toolbar, text="Database").grid(row=0, column=0, sticky="w")
        db_entry = ttk.Entry(toolbar, textvariable=self.db_path)
        db_entry.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(toolbar, text="Browse DB", command=self.choose_database).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(toolbar, text="New DB", command=self.create_database).grid(
            row=0, column=3, padx=(0, 8)
        )
        ttk.Button(toolbar, text="Init DB", command=self.initialize_workspace).grid(
            row=0, column=4, padx=(0, 8)
        )
        ttk.Button(toolbar, text="Delete DB File", command=self.delete_database_file).grid(
            row=0, column=5
        )

        filebar = ttk.Frame(self, padding=(10, 0, 10, 10))
        filebar.grid(row=1, column=0, sticky="ew")
        filebar.columnconfigure(1, weight=1)

        ttk.Label(filebar, text="Files Folder").grid(row=0, column=0, sticky="w")
        inbox_entry = ttk.Entry(filebar, textvariable=self.inbox_dir)
        inbox_entry.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(filebar, text="Browse Folder", command=self.choose_inbox).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(filebar, text="Project Records", command=self.show_project_records).grid(
            row=0, column=3, padx=(0, 8)
        )
        ttk.Button(filebar, text="Open Folder", command=self.open_current_folder).grid(
            row=0, column=4, padx=(0, 8)
        )
        ttk.Button(filebar, text="Index Folder", command=self.index_inbox).grid(
            row=0, column=5
        )

        main = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        data_frame = ttk.LabelFrame(main, text="Database Records", padding=8)
        data_frame.columnconfigure(0, weight=1)
        data_frame.rowconfigure(0, weight=1)
        main.add(data_frame, weight=4)

        columns = db.RECORD_COLUMNS
        self.tree = ttk.Treeview(
            data_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        column_widths = {
            "doc_id": 60,
            "doc_type": 80,
            "reference_number": 130,
            "filename": 180,
            "date_filed": 180,
            "date_indexed": 180,
            "storage_location": 260,
            "status": 120,
            "file_size_kb": 90,
            "notes": 220,
        }
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(
                column,
                width=column_widths.get(column, 120),
                minwidth=60,
                anchor="w",
            )

        y_scroll = ttk.Scrollbar(
            data_frame, orient=tk.VERTICAL, command=self.tree.yview
        )
        x_scroll = ttk.Scrollbar(
            data_frame, orient=tk.HORIZONTAL, command=self.tree.xview
        )
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        action_bar = ttk.Frame(data_frame)
        action_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(action_bar, text="Refresh", command=self.refresh_records).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(action_bar, text="Export CSV", command=lambda: self.export_db("csv")).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(action_bar, text="Export Excel", command=lambda: self.export_db("xlsx")).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(action_bar, text="Export PDF", command=lambda: self.export_db("pdf")).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(action_bar, text="Export DOC", command=lambda: self.export_db("doc")).pack(
            side=tk.LEFT, padx=(0, 16)
        )
        ttk.Button(action_bar, text="Delete Row", command=self.delete_selected_record).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(action_bar, text="Delete File", command=self.delete_selected_file).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(action_bar, text="Delete Row + File", command=self.delete_selected_record_and_file).pack(
            side=tk.LEFT
        )

        files_frame = ttk.LabelFrame(main, text="Files in Selected Folder", padding=8)
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)
        main.add(files_frame, weight=2)

        file_columns = ("name", "type", "size", "path")
        self.file_tree = ttk.Treeview(
            files_frame,
            columns=file_columns,
            show="headings",
            selectmode="browse",
        )
        file_widths = {"name": 220, "type": 80, "size": 100, "path": 520}
        for column in file_columns:
            self.file_tree.heading(column, text=column)
            self.file_tree.column(
                column,
                width=file_widths[column],
                minwidth=60,
                anchor="w",
            )
        file_y_scroll = ttk.Scrollbar(
            files_frame, orient=tk.VERTICAL, command=self.file_tree.yview
        )
        file_x_scroll = ttk.Scrollbar(
            files_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview
        )
        self.file_tree.configure(
            yscrollcommand=file_y_scroll.set,
            xscrollcommand=file_x_scroll.set,
        )
        self.file_tree.bind("<Double-1>", self.open_selected_folder_item)
        self.file_tree.grid(row=0, column=0, sticky="nsew")
        file_y_scroll.grid(row=0, column=1, sticky="ns")
        file_x_scroll.grid(row=1, column=0, sticky="ew")

        file_action_bar = ttk.Frame(files_frame)
        file_action_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        ttk.Button(file_action_bar, text="Refresh Files", command=self.refresh_files).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(file_action_bar, text="Up", command=self.go_to_parent_folder).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(file_action_bar, text="Open", command=self.open_selected_folder_item).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(file_action_bar, text="Convert File", command=self.convert_selected_folder_file).pack(
            side=tk.LEFT, padx=(0, 8)
        )
        ttk.Button(file_action_bar, text="Delete File", command=self.delete_selected_folder_file).pack(
            side=tk.LEFT
        )

        log_frame = ttk.LabelFrame(main, text="Workflow Log", padding=8)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main.add(log_frame, weight=2)

        self.log = tk.Text(log_frame, height=10, wrap="word")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")

        status = ttk.Label(self, textvariable=self.status_text, padding=(10, 0, 10, 8))
        status.grid(row=3, column=0, sticky="ew")

    def _set_active_database(self, path: Path) -> None:
        db_path = Path(path)
        db.set_db_path(db_path)
        config.BASE_DIR = db_path.parent
        config.DB_NAME = db_path.name
        self.db_path.set(str(db_path))
        if not self.inbox_dir.get():
            self.inbox_dir.set(str(db_path.parent / config.INBOX_DIR_NAME))

    def choose_database(self) -> None:
        selected = filedialog.askopenfilename(
            title="Choose SQLite database",
            initialdir=str(Path(self.db_path.get()).resolve().parent),
            filetypes=[("SQLite databases", "*.db *.sqlite *.sqlite3"), ("All files", "*.*")],
        )
        if selected:
            self._set_active_database(Path(selected))
            self.refresh_records()
            self.status_text.set(f"Viewing database: {selected}")

    def create_database(self) -> None:
        selected = filedialog.asksaveasfilename(
            title="Create SQLite database",
            initialdir=str(Path(self.db_path.get()).resolve().parent),
            initialfile=config.DB_NAME,
            defaultextension=".db",
            filetypes=[("SQLite databases", "*.db"), ("All files", "*.*")],
        )
        if not selected:
            return
        self._set_active_database(Path(selected))
        self.initialize_workspace(show_message=False)
        self.refresh_records()
        messagebox.showinfo("DMS", f"Database ready:\n{selected}")

    def choose_inbox(self) -> None:
        selected = filedialog.askdirectory(
            title="Choose inbox folder",
            initialdir=str(Path(self.inbox_dir.get()).resolve().parent),
        )
        if selected:
            self.inbox_dir.set(selected)
            self.refresh_files()
            self.status_text.set(f"Inbox selected: {selected}")

    def show_project_records(self) -> None:
        project_records = self._project_root() / "government_records"
        project_records.mkdir(parents=True, exist_ok=True)
        self.inbox_dir.set(str(project_records))
        self.refresh_files()
        self.status_text.set(f"Viewing project records folder: {project_records}")

    def open_current_folder(self) -> None:
        folder = Path(self.inbox_dir.get())
        if not folder.is_dir():
            messagebox.showwarning("DMS", f"Folder does not exist:\n{folder}")
            return
        os.startfile(folder)

    def go_to_parent_folder(self) -> None:
        folder = Path(self.inbox_dir.get())
        parent = folder.resolve().parent
        self.inbox_dir.set(str(parent))
        self.refresh_files()
        self.status_text.set(f"Viewing folder: {parent}")

    def initialize_workspace(self, show_message: bool = True) -> None:
        output = self._capture_output(self._init_workspace)
        self._append_log(output)
        self.status_text.set("Database and folders are ready")
        if show_message:
            messagebox.showinfo("DMS", "Database and folders are ready.")

    def _init_workspace(self) -> None:
        filesystem.ensure_directory_structure()
        db.init_db()

    def index_inbox(self) -> None:
        self._set_active_database(Path(self.db_path.get()))
        inbox = Path(self.inbox_dir.get())
        if not inbox.is_dir():
            messagebox.showerror("DMS", f"Inbox folder does not exist:\n{inbox}")
            return

        output = self._capture_output(lambda: pipeline.run_pipeline(inbox))
        self._append_log(output)
        self.refresh_records()
        self.refresh_files()
        self.status_text.set("Indexing complete")

    def refresh_records(self) -> None:
        self._set_active_database(Path(self.db_path.get()))
        self.records = db.fetch_records()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for record in self.records:
            values = [record.get(column, "") for column in db.RECORD_COLUMNS]
            self.tree.insert("", tk.END, values=values)

        self.status_text.set(f"Loaded {len(self.records)} database record(s)")

    def refresh_files(self) -> None:
        folder = Path(self.inbox_dir.get())
        self.folder_files = []
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        if not folder.is_dir():
            return

        for file_path in sorted(folder.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower())):
            stat = file_path.stat()
            record = {
                "name": file_path.name,
                "type": "(folder)" if file_path.is_dir() else file_path.suffix.lower() or "(none)",
                "size": "" if file_path.is_dir() else stat.st_size,
                "path": str(file_path),
            }
            self.folder_files.append(record)
            self.file_tree.insert(
                "",
                tk.END,
                values=(record["name"], record["type"], record["size"], record["path"]),
            )

        self.status_text.set(f"Loaded {len(self.folder_files)} file(s)")

    def delete_selected_record(self) -> None:
        record = self._selected_record()
        if not record:
            return
        if not messagebox.askyesno(
            "Delete database row",
            f"Delete this database row?\n\n{record.get('filename', '')}",
        ):
            return
        if db.delete_record(int(record["doc_id"])):
            self._append_log(f"Deleted database row: {record['doc_id']}")
            self.refresh_records()
        else:
            messagebox.showerror("DMS", "Could not delete the selected database row.")

    def delete_selected_file(self) -> bool:
        record = self._selected_record()
        if not record:
            return False
        storage_location = record.get("storage_location")
        if not storage_location:
            messagebox.showwarning("DMS", "This record has no file path.")
            return False
        file_path = self._resolve_record_file(storage_location)
        if not file_path.exists():
            messagebox.showwarning("DMS", f"File does not exist:\n{file_path}")
            return False
        if not messagebox.askyesno(
            "Delete file",
            f"Permanently delete this file?\n\n{file_path}",
        ):
            return False
        file_path.unlink()
        self._append_log(f"Deleted file: {file_path}")
        self.status_text.set(f"Deleted file: {file_path}")
        return True

    def delete_selected_record_and_file(self) -> None:
        record = self._selected_record()
        if not record:
            return
        if not messagebox.askyesno(
            "Delete row and file",
            f"Permanently delete the database row and archived file?\n\n{record.get('filename', '')}",
        ):
            return

        storage_location = record.get("storage_location")
        file_deleted = False
        if storage_location:
            file_path = self._resolve_record_file(storage_location)
            if file_path.exists():
                file_path.unlink()
                file_deleted = True
                self._append_log(f"Deleted file: {file_path}")

        row_deleted = db.delete_record(int(record["doc_id"]))
        self._append_log(
            f"Deleted row: {record['doc_id']} | file deleted: {file_deleted}"
        )
        if not row_deleted:
            messagebox.showerror("DMS", "Could not delete the selected database row.")
        self.refresh_records()

    def delete_database_file(self) -> None:
        db_file = Path(self.db_path.get())
        if not db_file.exists():
            messagebox.showwarning("DMS", f"Database file does not exist:\n{db_file}")
            return
        if not messagebox.askyesno(
            "Delete database file",
            f"Permanently delete this database file?\n\n{db_file}",
        ):
            return
        db_file.unlink()
        self._append_log(f"Deleted database file: {db_file}")
        self.refresh_records()
        self.status_text.set(f"Deleted database file: {db_file}")

    def _selected_record(self) -> dict | None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("DMS", "Select a database row first.")
            return None
        values = self.tree.item(selected[0], "values")
        return dict(zip(db.RECORD_COLUMNS, values))

    def _selected_folder_file(self) -> Path | None:
        selected = self.file_tree.selection()
        if not selected:
            messagebox.showwarning("DMS", "Select a file first.")
            return None
        values = self.file_tree.item(selected[0], "values")
        return Path(values[3])

    def open_selected_folder_item(self, event=None) -> None:
        file_path = self._selected_folder_file()
        if not file_path:
            return
        if not file_path.exists():
            messagebox.showwarning("DMS", f"File does not exist:\n{file_path}")
            return
        if file_path.is_dir():
            self.inbox_dir.set(str(file_path))
            self.refresh_files()
            self.status_text.set(f"Viewing folder: {file_path}")
            return
        os.startfile(file_path)

    def convert_selected_folder_file(self) -> None:
        file_path = self._selected_folder_file()
        if not file_path:
            return
        if not file_path.exists():
            messagebox.showwarning("DMS", f"File does not exist:\n{file_path}")
            return
        if file_path.is_dir():
            messagebox.showwarning("DMS", "Select a file to convert, not a folder.")
            return

        output_path = self._choose_file_conversion_path(file_path)
        if not output_path:
            return

        try:
            converted_path = conversion.convert_file(file_path, output_path)
        except Exception as error:
            messagebox.showerror("DMS", f"Could not convert file:\n{error}")
            return

        self._append_log(f"Converted file: {file_path} -> {converted_path}")
        self.status_text.set(f"Converted {converted_path}")
        messagebox.showinfo("DMS", f"Converted file saved:\n{converted_path}")

    def delete_selected_folder_file(self) -> None:
        file_path = self._selected_folder_file()
        if not file_path:
            return
        if not file_path.exists():
            messagebox.showwarning("DMS", f"File does not exist:\n{file_path}")
            return
        if file_path.is_dir():
            messagebox.showwarning("DMS", "Folder deletion is not available here. Open the folder and manage it in Explorer.")
            return
        if not messagebox.askyesno(
            "Delete file",
            f"Permanently delete this file?\n\n{file_path}",
        ):
            return
        file_path.unlink()
        self._append_log(f"Deleted folder file: {file_path}")
        self.refresh_files()

    def _choose_file_conversion_path(self, source_path: Path) -> Path | None:
        filetypes = [
            ("PDF files", "*.pdf"),
            ("Word documents", "*.doc"),
            ("Excel workbooks", "*.xlsx"),
            ("CSV files", "*.csv"),
            ("HTML files", "*.html"),
            ("Text files", "*.txt"),
            ("All files", "*.*"),
        ]
        selected = filedialog.asksaveasfilename(
            title="Convert file as",
            initialdir=str(source_path.parent.resolve()),
            initialfile=f"{source_path.stem}_converted.pdf",
            defaultextension=".pdf",
            filetypes=filetypes,
        )
        if not selected:
            return None
        return Path(selected)

    def _resolve_record_file(self, storage_location: str) -> Path:
        file_path = Path(storage_location)
        if file_path.is_absolute() or file_path.exists():
            return file_path
        return Path(self.db_path.get()).parent / file_path

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def export_db(self, format_name: str) -> None:
        records = db.fetch_records()
        if not records:
            messagebox.showwarning("DMS", "No database records to export.")
            return

        output_path = self._choose_export_path(format_name)
        if not output_path:
            return

        export_dir = config.BASE_DIR / config.EXPORT_DIR_NAME
        exporters = {
            "csv": export.export_records_to_csv,
            "xlsx": export.export_records_to_xlsx,
            "pdf": export.export_records_to_pdf,
            "doc": export.export_records_to_doc,
        }
        exporter = exporters[format_name]
        path = exporter(records, export_dir, output_path)
        if path:
            self._append_log(f"Exported {format_name.upper()}: {path}")
            self.status_text.set(f"Exported {path}")
            messagebox.showinfo("DMS", f"Export saved:\n{path}")

    def _choose_export_path(self, format_name: str) -> Path | None:
        details = {
            "csv": ("CSV file", ".csv", [("CSV files", "*.csv")]),
            "xlsx": ("Excel workbook", ".xlsx", [("Excel workbooks", "*.xlsx")]),
            "pdf": ("PDF report", ".pdf", [("PDF files", "*.pdf")]),
            "doc": ("Word document", ".doc", [("Word documents", "*.doc")]),
        }
        label, extension, filetypes = details[format_name]
        export_dir = config.BASE_DIR / config.EXPORT_DIR_NAME

        selected = filedialog.asksaveasfilename(
            title=f"Save {label}",
            initialdir=str(Path(self.db_path.get()).parent.resolve()),
            initialfile=f"document_records{extension}",
            defaultextension=extension,
            filetypes=filetypes + [("All files", "*.*")],
        )
        if not selected:
            return None
        return Path(selected)

    def _capture_output(self, action) -> str:
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            action()
        return stream.getvalue().strip()

    def _append_log(self, message: str) -> None:
        if not message:
            return
        self.log.insert(tk.END, message + "\n\n")
        self.log.see(tk.END)


def main() -> None:
    app = DmsApp()
    app.mainloop()


if __name__ == "__main__":
    main()
