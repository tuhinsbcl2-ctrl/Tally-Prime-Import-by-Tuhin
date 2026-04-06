"""Sales vouchers tab."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

import pandas as pd

from tally_importer import excel_reader
from tally_importer.gui.export_helpers import build_error_detail, format_error_lines
from tally_importer.gui.mapping_dialog import MappingDialog
from tally_importer.validator import validate_sales
from tally_importer.xml_generator import build_sales_xml


class SalesTab(ttk.Frame):
    """Tab for importing sales invoices."""

    def __init__(self, parent: ttk.Notebook) -> None:
        super().__init__(parent)
        self._df: pd.DataFrame | None = None
        self._mapping: dict[str, str] = {}
        self._file_path = ""
        self._sheet_name = ""
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Label(top, text="Excel File:").grid(row=0, column=0, sticky="w", pady=3)
        self._file_var = tk.StringVar()
        ttk.Entry(top, textvariable=self._file_var, width=50, state="readonly").grid(
            row=0, column=1, padx=4, sticky="ew"
        )
        ttk.Button(top, text="Browse…", command=self._browse).grid(row=0, column=2)

        ttk.Label(top, text="Sheet:").grid(row=1, column=0, sticky="w", pady=3)
        self._sheet_var = tk.StringVar()
        self._sheet_combo = ttk.Combobox(
            top, textvariable=self._sheet_var, state="readonly", width=24
        )
        self._sheet_combo.grid(row=1, column=1, sticky="w", padx=4)
        self._sheet_combo.bind("<<ComboboxSelected>>", self._load_sheet)

        # Default voucher type
        ttk.Label(top, text="Default Voucher Type:").grid(
            row=2, column=0, sticky="w", pady=3
        )
        self._default_vtype = tk.StringVar(value="Sales")
        ttk.Entry(top, textvariable=self._default_vtype, width=24).grid(
            row=2, column=1, sticky="w", padx=4
        )

        # GST ledger name settings
        ttk.Label(top, text="CGST Ledger Name:").grid(row=3, column=0, sticky="w", pady=3)
        self._cgst_ledger = tk.StringVar(value="Output CGST")
        ttk.Entry(top, textvariable=self._cgst_ledger, width=24).grid(
            row=3, column=1, sticky="w", padx=4
        )

        ttk.Label(top, text="SGST Ledger Name:").grid(row=4, column=0, sticky="w", pady=3)
        self._sgst_ledger = tk.StringVar(value="Output SGST")
        ttk.Entry(top, textvariable=self._sgst_ledger, width=24).grid(
            row=4, column=1, sticky="w", padx=4
        )

        ttk.Label(top, text="IGST Ledger Name:").grid(row=5, column=0, sticky="w", pady=3)
        self._igst_ledger = tk.StringVar(value="Output IGST")
        ttk.Entry(top, textvariable=self._igst_ledger, width=24).grid(
            row=5, column=1, sticky="w", padx=4
        )

        ttk.Label(top, text="Round Off Ledger Name:").grid(row=6, column=0, sticky="w", pady=3)
        self._round_off_ledger = tk.StringVar(value="Round Off")
        ttk.Entry(top, textvariable=self._round_off_ledger, width=24).grid(
            row=6, column=1, sticky="w", padx=4
        )

        top.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(self, padding=(8, 0, 8, 4))
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Map Columns…", command=self._open_mapping).pack(
            side="left", padx=2
        )
        ttk.Button(btn_frame, text="Validate & Preview", command=self._validate).pack(
            side="left", padx=2
        )
        ttk.Button(btn_frame, text="Export XML…", command=self._export).pack(
            side="left", padx=2
        )

        preview_frame = ttk.LabelFrame(self, text="Preview (first 50 rows)", padding=4)
        preview_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self._tree = self._make_tree(preview_frame)

        status_frame = ttk.LabelFrame(self, text="Validation Messages", padding=4)
        status_frame.pack(fill="x", padx=8, pady=(0, 8))
        self._status_text = tk.Text(
            status_frame, height=6, state="disabled", wrap="word",
            bg="#f8f8f8", relief="flat"
        )
        scroll = ttk.Scrollbar(
            status_frame, orient="vertical", command=self._status_text.yview
        )
        self._status_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self._status_text.pack(fill="both", expand=True)

    def _make_tree(self, parent: ttk.Frame) -> ttk.Treeview:
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)
        return tree

    # ------------------------------------------------------------------
    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")],
        )
        if not path:
            return
        self._file_path = path
        self._file_var.set(path)
        try:
            sheets = excel_reader.read_excel_sheets(path)
            self._sheet_combo.configure(values=sheets)
            if sheets:
                self._sheet_combo.set(sheets[0])
                self._load_sheet()
        except Exception as exc:
            messagebox.showerror("Error", f"Could not open file:\n{exc}")

    def _load_sheet(self, _event: Any = None) -> None:
        sheet = self._sheet_var.get()
        if not sheet or not self._file_path:
            return
        try:
            self._df = excel_reader.read_sheet(self._file_path, sheet)
            self._sheet_name = sheet
            self._refresh_tree()
            self._log(f"Loaded {len(self._df)} rows from sheet '{sheet}'.")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not load sheet:\n{exc}")

    def _open_mapping(self) -> None:
        if self._df is None:
            messagebox.showwarning("Mapping", "Load an Excel file first.")
            return
        from tally_importer.mapping import SALES_FIELDS

        dlg = MappingDialog(
            self,
            "sales",
            SALES_FIELDS,
            excel_reader.get_columns(self._df),
            self._mapping,
        )
        self.wait_window(dlg)
        if dlg.result is not None:
            self._mapping = dlg.result
            self._log("Column mapping updated.")

    def _validate(self) -> None:
        if self._df is None:
            messagebox.showwarning("Validate", "Load an Excel file first.")
            return
        rows = self._df.fillna("").to_dict(orient="records")
        valid, errors = validate_sales(
            rows, self._mapping, self._default_vtype.get(),
            cgst_ledger=self._cgst_ledger.get(),
            sgst_ledger=self._sgst_ledger.get(),
            igst_ledger=self._igst_ledger.get(),
            round_off_ledger=self._round_off_ledger.get(),
        )
        msgs: list[str] = []
        if errors:
            for e in errors:
                msgs.append(f"Row {e['row']}: " + "; ".join(e["errors"]))
        if valid:
            msgs.append(f"\n✔  {len(valid)} valid sales entries ready to export.")
        self._log("\n".join(msgs) if msgs else "No data to validate.")

    def _export(self) -> None:
        if self._df is None:
            messagebox.showwarning("Export", "Load an Excel file first.")
            return
        rows = self._df.fillna("").to_dict(orient="records")
        valid, errors = validate_sales(
            rows, self._mapping, self._default_vtype.get(),
            cgst_ledger=self._cgst_ledger.get(),
            sgst_ledger=self._sgst_ledger.get(),
            igst_ledger=self._igst_ledger.get(),
            round_off_ledger=self._round_off_ledger.get(),
        )
        if not valid:
            messagebox.showwarning(
                "Export", "No valid entries to export.\nCheck validation messages."
            )
            return
        if errors:
            self._log("\n".join(format_error_lines(errors)))
            detail = build_error_detail(errors)
            proceed = messagebox.askyesno(
                "Validation Warnings",
                f"{len(errors)} row(s) have errors and will be skipped:\n\n"
                f"{detail}\n\n"
                f"Export the {len(valid)} valid rows?",
            )
            if not proceed:
                return

        path = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("XML Files", "*.xml"), ("All Files", "*.*")],
            title="Save Sales Vouchers XML",
        )
        if not path:
            return
        try:
            xml_content = build_sales_xml(valid)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                fh.write(xml_content)
            messagebox.showinfo(
                "Export Complete", f"Exported {len(valid)} sales voucher(s) to:\n{path}"
            )
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    # ------------------------------------------------------------------
    def _refresh_tree(self) -> None:
        if self._df is None:
            return
        cols = list(self._df.columns)
        self._tree.configure(columns=cols)
        for col in cols:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=100, minwidth=60, stretch=True)
        self._tree.delete(*self._tree.get_children())
        for _, row in self._df.head(50).iterrows():
            self._tree.insert("", "end", values=list(row.fillna("")))

    def _log(self, message: str) -> None:
        self._status_text.configure(state="normal")
        self._status_text.delete("1.0", "end")
        self._status_text.insert("end", message)
        self._status_text.configure(state="disabled")
