import contextlib
import io
import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dms import config, db, export, filesystem, pipeline


class DmsApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Municipal Document Management System")
        self.geometry("1180x720")
        self.minsize(960, 620)

        self.inbox_dir = tk.StringVar(
            value=str(config.BASE_DIR / config.INBOX_DIR_NAME)
        )
        self.status_text = tk.StringVar(value="Ready")

        self._build_layout()
        self.initialize_workspace(show_message=False)
        self.refresh_records()

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self, padding=10)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(1, weight=1)

        ttk.Label(toolbar, text="Inbox").grid(row=0, column=0, sticky="w")
        inbox_entry = ttk.Entry(toolbar, textvariable=self.inbox_dir)
        inbox_entry.grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(toolbar, text="Browse", command=self.choose_inbox).grid(
            row=0, column=2, padx=(0, 8)
        )
        ttk.Button(toolbar, text="Add Files", command=self.add_files_to_inbox).grid(
            row=0, column=3, padx=(0, 8)
        )
        ttk.Button(toolbar, text="Init DB", command=self.initialize_workspace).grid(
            row=0, column=4, padx=(0, 8)
        )
        ttk.Button(toolbar, text="Index Inbox", command=self.index_inbox).grid(
            row=0, column=5
        )

        main = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

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
        status.grid(row=2, column=0, sticky="ew")

    def choose_inbox(self) -> None:
        selected = filedialog.askdirectory(
            title="Choose inbox folder",
            initialdir=str(Path(self.inbox_dir.get()).resolve().parent),
        )
        if selected:
            self.inbox_dir.set(selected)
            self.status_text.set(f"Inbox selected: {selected}")

    def add_files_to_inbox(self) -> None:
        filetypes = [
            ("Supported documents", "*.pdf *.doc *.docx *.xls *.xlsx *.csv"),
            ("All files", "*.*"),
        ]
        selected_files = filedialog.askopenfilenames(
            title="Add files to inbox",
            filetypes=filetypes,
        )
        if not selected_files:
            return

        inbox = Path(self.inbox_dir.get())
        inbox.mkdir(parents=True, exist_ok=True)
        copied = 0
        skipped = 0
        for file_name in selected_files:
            source = Path(file_name)
            if source.suffix.lower() not in config.SUPPORTED_EXTENSIONS:
                skipped += 1
                continue
            shutil.copy2(source, inbox / source.name)
            copied += 1

        self._append_log(f"Added {copied} file(s) to {inbox}. Skipped {skipped}.")
        self.status_text.set(f"Added {copied} file(s) to inbox")

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
        inbox = Path(self.inbox_dir.get())
        if not inbox.is_dir():
            messagebox.showerror("DMS", f"Inbox folder does not exist:\n{inbox}")
            return

        output = self._capture_output(lambda: pipeline.run_pipeline(inbox))
        self._append_log(output)
        self.refresh_records()
        self.status_text.set("Indexing complete")

    def refresh_records(self) -> None:
        self.records = db.fetch_records()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for record in self.records:
            values = [record.get(column, "") for column in db.RECORD_COLUMNS]
            self.tree.insert("", tk.END, values=values)

        self.status_text.set(f"Loaded {len(self.records)} database record(s)")

    def export_db(self, format_name: str) -> None:
        records = db.fetch_records()
        if not records:
            messagebox.showwarning("DMS", "No database records to export.")
            return

        export_dir = config.BASE_DIR / config.EXPORT_DIR_NAME
        exporters = {
            "csv": export.export_records_to_csv,
            "xlsx": export.export_records_to_xlsx,
            "pdf": export.export_records_to_pdf,
            "doc": export.export_records_to_doc,
        }
        exporter = exporters[format_name]
        path = exporter(records, export_dir)
        if path:
            self._append_log(f"Exported {format_name.upper()}: {path}")
            self.status_text.set(f"Exported {path}")
            messagebox.showinfo("DMS", f"Export saved:\n{path}")

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
