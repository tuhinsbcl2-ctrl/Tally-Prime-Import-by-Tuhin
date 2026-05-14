"""Sales itemwise vouchers tab with dynamic line item management."""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

import pandas as pd

from tally_importer import excel_reader
from tally_importer.gui.export_helpers import build_error_detail, format_error_lines
from tally_importer.gui.mapping_dialog import MappingDialog
from tally_importer.validator import validate_sales_itemwise, VALID_UQC_CODES
from tally_importer.xml_generator import build_sales_itemwise_xml


class SalesItemwiseTab(ttk.Frame):
    """Tab for importing sales invoices with multiple itemwise details."""

    def __init__(self, parent: ttk.Notebook) -> None:
        super().__init__(parent)
        self._df: pd.DataFrame | None = None
        self._mapping: dict[str, str] = {}
        self._file_path = ""
        self._sheet_name = ""
        self._line_items: list[dict[str, Any]] = []  # In-memory line items
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Build the user interface."""
        # ===== INVOICE HEADER SECTION =====
        header_frame = ttk.LabelFrame(self, text="Invoice Header", padding=8)
        header_frame.pack(fill="x", padx=8, pady=4)

        # Row 1: Date, Invoice Number
        ttk.Label(header_frame, text="Date (DD-MM-YYYY):").grid(row=0, column=0, sticky="w", pady=3)
        self._date_var = tk.StringVar()
        ttk.Entry(header_frame, textvariable=self._date_var, width=15).grid(row=0, column=1, sticky="w", padx=4)

        ttk.Label(header_frame, text="Invoice Number:").grid(row=0, column=2, sticky="w", pady=3)
        self._invoice_var = tk.StringVar()
        ttk.Entry(header_frame, textvariable=self._invoice_var, width=15).grid(row=0, column=3, sticky="w", padx=4)

        # Row 2: Party Name, GST Number
        ttk.Label(header_frame, text="Party Name / Customer:").grid(row=1, column=0, sticky="w", pady=3)
        self._party_var = tk.StringVar()
        ttk.Entry(header_frame, textvariable=self._party_var, width=25).grid(row=1, column=1, sticky="ew", padx=4)

        ttk.Label(header_frame, text="GST Number:").grid(row=1, column=2, sticky="w", pady=3)
        self._gst_number_var = tk.StringVar()
        ttk.Entry(header_frame, textvariable=self._gst_number_var, width=20).grid(row=1, column=3, sticky="ew", padx=4)

        # Row 3: Sales Ledger, Place of Supply
        ttk.Label(header_frame, text="Sales Ledger:").grid(row=2, column=0, sticky="w", pady=3)
        self._sales_ledger_var = tk.StringVar(value="Sales")
        ttk.Entry(header_frame, textvariable=self._sales_ledger_var, width=25).grid(
            row=2, column=1, sticky="ew", padx=4
        )

        ttk.Label(header_frame, text="Place of Supply (State):").grid(row=2, column=2, sticky="w", pady=3)
        self._place_of_supply_var = tk.StringVar()
        ttk.Entry(header_frame, textvariable=self._place_of_supply_var, width=20).grid(
            row=2, column=3, sticky="ew", padx=4
        )

        # Row 4: Narration
        ttk.Label(header_frame, text="Narration / Description:").grid(row=3, column=0, sticky="w", pady=3)
        self._narration_var = tk.StringVar()
        ttk.Entry(header_frame, textvariable=self._narration_var, width=60).grid(
            row=3, column=1, columnspan=3, sticky="ew", padx=4
        )

        header_frame.columnconfigure(1, weight=1)
        header_frame.columnconfigure(3, weight=1)

        # ===== GST LEDGER CONFIGURATION =====
        gst_frame = ttk.LabelFrame(self, text="GST Ledger Names", padding=8)
        gst_frame.pack(fill="x", padx=8, pady=4)

        ttk.Label(gst_frame, text="CGST Ledger:").grid(row=0, column=0, sticky="w", pady=2)
        self._cgst_ledger = tk.StringVar(value="Output CGST")
        ttk.Entry(gst_frame, textvariable=self._cgst_ledger, width=20).grid(row=0, column=1, sticky="w", padx=4)

        ttk.Label(gst_frame, text="SGST Ledger:").grid(row=0, column=2, sticky="w", pady=2)
        self._sgst_ledger = tk.StringVar(value="Output SGST")
        ttk.Entry(gst_frame, textvariable=self._sgst_ledger, width=20).grid(row=0, column=3, sticky="w", padx=4)

        ttk.Label(gst_frame, text="IGST Ledger:").grid(row=1, column=0, sticky="w", pady=2)
        self._igst_ledger = tk.StringVar(value="Output IGST")
        ttk.Entry(gst_frame, textvariable=self._igst_ledger, width=20).grid(row=1, column=1, sticky="w", padx=4)

        ttk.Label(gst_frame, text="Round Off Ledger:").grid(row=1, column=2, sticky="w", pady=2)
        self._round_off_ledger = tk.StringVar(value="Round Off")
        ttk.Entry(gst_frame, textvariable=self._round_off_ledger, width=20).grid(row=1, column=3, sticky="w", padx=4)

        # ===== LINE ITEMS SECTION =====
        items_frame = ttk.LabelFrame(self, text="Line Items", padding=4)
        items_frame.pack(fill="both", expand=True, padx=8, pady=4)

        # Buttons
        btn_frame = ttk.Frame(items_frame)
        btn_frame.pack(fill="x", pady=4)
        ttk.Button(btn_frame, text="➕ Add Item", command=self._add_item).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ Remove Selected", command=self._remove_item).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📂 Load from Excel", command=self._load_from_excel).pack(side="left", padx=2)

        # Treeview for line items
        self._items_tree = self._make_items_tree(items_frame)

        # ===== INVOICE TOTALS =====
        totals_frame = ttk.LabelFrame(self, text="Invoice Totals", padding=8)
        totals_frame.pack(fill="x", padx=8, pady=4)

        ttk.Label(totals_frame, text="Total Taxable:").grid(row=0, column=0, sticky="w", padx=4)
        self._total_taxable_var = tk.StringVar(value="₹ 0.00")
        ttk.Label(totals_frame, textvariable=self._total_taxable_var, font=("", 10, "bold")).grid(
            row=0, column=1, sticky="w", padx=4
        )

        ttk.Label(totals_frame, text="Total CGST:").grid(row=0, column=2, sticky="w", padx=4)
        self._total_cgst_var = tk.StringVar(value="₹ 0.00")
        ttk.Label(totals_frame, textvariable=self._total_cgst_var, font=("", 10, "bold")).grid(
            row=0, column=3, sticky="w", padx=4
        )

        ttk.Label(totals_frame, text="Total SGST:").grid(row=0, column=4, sticky="w", padx=4)
        self._total_sgst_var = tk.StringVar(value="₹ 0.00")
        ttk.Label(totals_frame, textvariable=self._total_sgst_var, font=("", 10, "bold")).grid(
            row=0, column=5, sticky="w", padx=4
        )

        ttk.Label(totals_frame, text="Total IGST:").grid(row=1, column=0, sticky="w", padx=4)
        self._total_igst_var = tk.StringVar(value="₹ 0.00")
        ttk.Label(totals_frame, textvariable=self._total_igst_var, font=("", 10, "bold")).grid(
            row=1, column=1, sticky="w", padx=4
        )

        ttk.Label(totals_frame, text="Grand Total:").grid(row=1, column=2, sticky="w", padx=4)
        self._grand_total_var = tk.StringVar(value="₹ 0.00")
        ttk.Label(
            totals_frame, textvariable=self._grand_total_var, font=("", 12, "bold"), foreground="darkgreen"
        ).grid(row=1, column=3, sticky="w", padx=4)

        # ===== ACTION BUTTONS =====
        action_frame = ttk.Frame(self, padding=8)
        action_frame.pack(fill="x")
        ttk.Button(action_frame, text="Map Columns…", command=self._open_mapping).pack(side="left", padx=2)
        ttk.Button(action_frame, text="Validate & Preview", command=self._validate).pack(side="left", padx=2)
        ttk.Button(action_frame, text="Export XML…", command=self._export).pack(side="left", padx=2)

        # ===== STATUS MESSAGES =====
        status_frame = ttk.LabelFrame(self, text="Validation Messages", padding=4)
        status_frame.pack(fill="x", padx=8, pady=(0, 8))
        self._status_text = tk.Text(
            status_frame, height=5, state="disabled", wrap="word", bg="#f8f8f8", relief="flat"
        )
        scroll = ttk.Scrollbar(status_frame, orient="vertical", command=self._status_text.yview)
        self._status_text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self._status_text.pack(fill="both", expand=True)

    def _make_items_tree(self, parent: ttk.Frame) -> ttk.Treeview:
        """Create the line items treeview."""
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        columns = (
            "Item Name",
            "HSN",
            "Qty",
            "UQC",
            "Rate",
            "Taxable",
            "GST%",
            "CGST",
            "SGST",
            "IGST",
            "Remarks",
        )
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse", height=10)

        # Define headings and widths
        widths = {
            "Item Name": 120,
            "HSN": 70,
            "Qty": 50,
            "UQC": 60,
            "Rate": 80,
            "Taxable": 90,
            "GST%": 60,
            "CGST": 80,
            "SGST": 80,
            "IGST": 80,
            "Remarks": 100,
        }

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=widths.get(col, 80), minwidth=50)

        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tree.pack(fill="both", expand=True)

        # Bind double-click to edit
        tree.bind("<Double-1>", self._on_double_click)

        return tree

    def _add_item(self) -> None:
        """Add a new line item row."""
        item = {
            "item_name": "",
            "hsn_code": "",
            "qty": 0.0,
            "uqc": "Pcs",
            "rate": 0.0,
            "gst_rate": 0.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "igst": 0.0,
            "remarks": "",
        }
        self._line_items.append(item)
        self._refresh_items_tree()
        self._log("✅ New item row added.")

    def _remove_item(self) -> None:
        """Remove selected line item."""
        selection = self._items_tree.selection()
        if not selection:
            messagebox.showwarning("Remove Item", "Please select an item to remove.")
            return

        item_id = selection[0]
        item_index = int(item_id) - 1

        if 0 <= item_index < len(self._line_items):
            self._line_items.pop(item_index)
            self._refresh_items_tree()
            self._log("✅ Item removed.")

    def _on_double_click(self, event: Any) -> None:
        """Handle double-click to edit item."""
        item_id = self._items_tree.selection()
        if not item_id:
            return

        item_id = item_id[0]
        item_index = int(item_id) - 1

        if not (0 <= item_index < len(self._line_items)):
            return

        # Create edit dialog
        self._edit_item_dialog(item_index)

    def _edit_item_dialog(self, item_index: int) -> None:
        """Show dialog to edit line item."""
        item = self._line_items[item_index]

        dlg = tk.Toplevel(self)
        dlg.title("Edit Line Item")
        dlg.geometry("500x400")
        dlg.transient(self)
        dlg.grab_set()

        # Create fields
        fields = {}

        ttk.Label(dlg, text="Item Name:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        fields["item_name"] = tk.StringVar(value=item["item_name"])
        ttk.Entry(dlg, textvariable=fields["item_name"], width=40).grid(row=0, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(dlg, text="HSN/SAC Code:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        fields["hsn_code"] = tk.StringVar(value=item["hsn_code"])
        ttk.Entry(dlg, textvariable=fields["hsn_code"], width=40).grid(row=1, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(dlg, text="Quantity:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        fields["qty"] = tk.StringVar(value=str(item["qty"]))
        ttk.Entry(dlg, textvariable=fields["qty"], width=40).grid(row=2, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(dlg, text="UQC (Unit):").grid(row=3, column=0, sticky="w", padx=8, pady=4)
        fields["uqc"] = tk.StringVar(value=item["uqc"])
        uqc_combo = ttk.Combobox(
            dlg, textvariable=fields["uqc"], values=list(VALID_UQC_CODES.keys()), state="readonly", width=37
        )
        uqc_combo.grid(row=3, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(dlg, text="Rate per Unit:").grid(row=4, column=0, sticky="w", padx=8, pady=4)
        fields["rate"] = tk.StringVar(value=str(item["rate"]))
        ttk.Entry(dlg, textvariable=fields["rate"], width=40).grid(row=4, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(dlg, text="GST Rate (%):").grid(row=5, column=0, sticky="w", padx=8, pady=4)
        fields["gst_rate"] = tk.StringVar(value=str(item["gst_rate"]))
        ttk.Entry(dlg, textvariable=fields["gst_rate"], width=40).grid(row=5, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(dlg, text="CGST Amount:").grid(row=6, column=0, sticky="w", padx=8, pady=4)
        fields["cgst"] = tk.StringVar(value=str(item["cgst"]))
        ttk.Entry(dlg, textvariable=fields["cgst"], width=40).grid(row=6, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(dlg, text="SGST Amount:").grid(row=7, column=0, sticky="w", padx=8, pady=4)
        fields["sgst"] = tk.StringVar(value=str(item["sgst"]))
        ttk.Entry(dlg, textvariable=fields["sgst"], width=40).grid(row=7, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(dlg, text="IGST Amount:").grid(row=8, column=0, sticky="w", padx=8, pady=4)
        fields["igst"] = tk.StringVar(value=str(item["igst"]))
        ttk.Entry(dlg, textvariable=fields["igst"], width=40).grid(row=8, column=1, sticky="ew", padx=8, pady=4)

        ttk.Label(dlg, text="Remarks:").grid(row=9, column=0, sticky="w", padx=8, pady=4)
        fields["remarks"] = tk.StringVar(value=item["remarks"])
        ttk.Entry(dlg, textvariable=fields["remarks"], width=40).grid(row=9, column=1, sticky="ew", padx=8, pady=4)

        # Buttons
        def save():
            try:
                self._line_items[item_index]["item_name"] = fields["item_name"].get()
                self._line_items[item_index]["hsn_code"] = fields["hsn_code"].get()
                self._line_items[item_index]["qty"] = float(fields["qty"].get() or 0)
                self._line_items[item_index]["uqc"] = fields["uqc"].get()
                self._line_items[item_index]["rate"] = float(fields["rate"].get() or 0)
                self._line_items[item_index]["gst_rate"] = float(fields["gst_rate"].get() or 0)
                self._line_items[item_index]["cgst"] = float(fields["cgst"].get() or 0)
                self._line_items[item_index]["sgst"] = float(fields["sgst"].get() or 0)
                self._line_items[item_index]["igst"] = float(fields["igst"].get() or 0)
                self._line_items[item_index]["remarks"] = fields["remarks"].get()
                self._refresh_items_tree()
                dlg.destroy()
                self._log("✅ Item updated.")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {e}")

        btn_frame = ttk.Frame(dlg)
        btn_frame.grid(row=10, column=0, columnspan=2, pady=16)
        ttk.Button(btn_frame, text="Save", command=save).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side="left", padx=4)

        dlg.columnconfigure(1, weight=1)

    def _refresh_items_tree(self) -> None:
        """Refresh the items tree display."""
        self._items_tree.delete(*self._items_tree.get_children())

        for i, item in enumerate(self._line_items, start=1):
            qty = item.get("qty", 0)
            rate = item.get("rate", 0)
            taxable = round(qty * rate, 2) if qty > 0 and rate > 0 else 0.0

            values = (
                item.get("item_name", ""),
                item.get("hsn_code", ""),
                f"{qty:.2f}",
                item.get("uqc", ""),
                f"{rate:.2f}",
                f"₹ {taxable:.2f}",
                f"{item.get('gst_rate', 0):.1f}%",
                f"₹ {item.get('cgst', 0):.2f}",
                f"₹ {item.get('sgst', 0):.2f}",
                f"₹ {item.get('igst', 0):.2f}",
                item.get("remarks", ""),
            )
            self._items_tree.insert("", "end", iid=str(i), values=values)

        self._update_totals()

    def _update_totals(self) -> None:
        """Update invoice totals display."""
        total_taxable = 0.0
        total_cgst = 0.0
        total_sgst = 0.0
        total_igst = 0.0

        for item in self._line_items:
            qty = item.get("qty", 0)
            rate = item.get("rate", 0)
            taxable = qty * rate
            total_taxable += taxable
            total_cgst += item.get("cgst", 0)
            total_sgst += item.get("sgst", 0)
            total_igst += item.get("igst", 0)

        total_taxable = round(total_taxable, 2)
        total_cgst = round(total_cgst, 2)
        total_sgst = round(total_sgst, 2)
        total_igst = round(total_igst, 2)
        grand_total = round(total_taxable + total_cgst + total_sgst + total_igst, 2)

        self._total_taxable_var.set(f"₹ {total_taxable:.2f}")
        self._total_cgst_var.set(f"₹ {total_cgst:.2f}")
        self._total_sgst_var.set(f"₹ {total_sgst:.2f}")
        self._total_igst_var.set(f"₹ {total_igst:.2f}")
        self._grand_total_var.set(f"₹ {grand_total:.2f}")

    def _load_from_excel(self) -> None:
        """Load line items from Excel file."""
        path = filedialog.askopenfilename(
            title="Select Excel File with Line Items",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")],
        )
        if not path:
            return

        try:
            sheets = excel_reader.read_excel_sheets(path)
            if not sheets:
                messagebox.showerror("Error", "No sheets found in Excel file.")
                return

            # Show sheet selection dialog
            sheet_dlg = tk.Toplevel(self)
            sheet_dlg.title("Select Sheet")
            sheet_dlg.geometry("300x150")
            sheet_dlg.transient(self)
            sheet_dlg.grab_set()

            ttk.Label(sheet_dlg, text="Select worksheet:").pack(padx=10, pady=10)
            sheet_var = tk.StringVar(value=sheets[0])
            sheet_combo = ttk.Combobox(sheet_dlg, textvariable=sheet_var, values=sheets, state="readonly", width=30)
            sheet_combo.pack(padx=10, pady=5)

            def load_sheet():
                df = excel_reader.read_sheet(path, sheet_var.get())
                self._line_items = df.to_dict(orient="records")
                self._refresh_items_tree()
                sheet_dlg.destroy()
                self._log(f"✅ Loaded {len(self._line_items)} items from Excel.")

            ttk.Button(sheet_dlg, text="Load", command=load_sheet).pack(pady=10)

        except Exception as exc:
            messagebox.showerror("Error", f"Could not load Excel file:\n{exc}")

    def _open_mapping(self) -> None:
        """Open column mapping dialog."""
        if self._df is None:
            messagebox.showwarning("Mapping", "Load an Excel file first.")
            return

        from tally_importer.mapping import SALES_ITEMWISE_FIELDS

        dlg = MappingDialog(
            self,
            "sales_itemwise",
            SALES_ITEMWISE_FIELDS,
            excel_reader.get_columns(self._df) if self._df is not None else [],
            self._mapping,
        )
        self.wait_window(dlg)
        if dlg.result is not None:
            self._mapping = dlg.result
            self._log("✅ Column mapping updated.")

    def _validate(self) -> None:
        """Validate current invoice."""
        if not self._line_items:
            messagebox.showwarning("Validate", "Add at least one line item.")
            return

        # Create invoice data structure
        invoice_data = {
            "date": self._date_var.get(),
            "invoice_number": self._invoice_var.get(),
            "party_name": self._party_var.get(),
            "entry_date": self._date_var.get(),
            "original_date": self._date_var.get(),
            "sales_ledger": self._sales_ledger_var.get(),
            "gst_number": self._gst_number_var.get(),
            "place_of_supply": self._place_of_supply_var.get(),
            "narration": self._narration_var.get(),
            "voucher_type": "Sales",
        }

        # Validate header
        errors = []
        if not invoice_data["date"]:
            errors.append("Missing invoice date")
        if not invoice_data["invoice_number"]:
            errors.append("Missing invoice number")
        if not invoice_data["party_name"]:
            errors.append("Missing party name")
        if not invoice_data["sales_ledger"]:
            errors.append("Missing sales ledger")

        if errors:
            self._log("\n".join([f"❌ {e}" for e in errors]))
            return

        # Create rows for validation
        rows = [
            {**invoice_data, **item}
            for item in self._line_items
        ]

        # Validate using itemwise validator
        valid, val_errors = validate_sales_itemwise(
            rows,
            {
                "date": "date",
                "invoice_number": "invoice_number",
                "party_name": "party_name",
                "entry_date": "entry_date",
                "original_date": "original_date",
                "sales_ledger": "sales_ledger",
                "gst_number": "gst_number",
                "place_of_supply": "place_of_supply",
                "narration": "narration",
                "voucher_type": "voucher_type",
                "item_name": "item_name",
                "hsn_code": "hsn_code",
                "qty": "qty",
                "uqc": "uqc",
                "rate": "rate",
                "gst_rate": "gst_rate",
                "cgst": "cgst",
                "sgst": "sgst",
                "igst": "igst",
                "remarks": "remarks",
            },
            cgst_ledger=self._cgst_ledger.get(),
            sgst_ledger=self._sgst_ledger.get(),
            igst_ledger=self._igst_ledger.get(),
            round_off_ledger=self._round_off_ledger.get(),
        )

        msgs = []
        if val_errors:
            for e in val_errors:
                msgs.append(f"Row {e['row']}: " + "; ".join(e["errors"]))
        if valid:
            msgs.append(f"\n✅ {len(valid)} valid invoice(s) ready to export.")
            msgs.append(f"   Total: ₹{valid[0].total_amount:.2f}")

        self._log("\n".join(msgs) if msgs else "No data to validate.")

    def _export(self) -> None:
        """Export invoice to XML."""
        if not self._line_items:
            messagebox.showwarning("Export", "Add at least one line item.")
            return

        # Validate first
        invoice_data = {
            "date": self._date_var.get(),
            "invoice_number": self._invoice_var.get(),
            "party_name": self._party_var.get(),
            "entry_date": self._date_var.get(),
            "original_date": self._date_var.get(),
            "sales_ledger": self._sales_ledger_var.get(),
            "gst_number": self._gst_number_var.get(),
            "place_of_supply": self._place_of_supply_var.get(),
            "narration": self._narration_var.get(),
            "voucher_type": "Sales",
        }

        rows = [
            {**invoice_data, **item}
            for item in self._line_items
        ]

        valid, val_errors = validate_sales_itemwise(
            rows,
            {
                "date": "date",
                "invoice_number": "invoice_number",
                "party_name": "party_name",
                "entry_date": "entry_date",
                "original_date": "original_date",
                "sales_ledger": "sales_ledger",
                "gst_number": "gst_number",
                "place_of_supply": "place_of_supply",
                "narration": "narration",
                "voucher_type": "voucher_type",
                "item_name": "item_name",
                "hsn_code": "hsn_code",
                "qty": "qty",
                "uqc": "uqc",
                "rate": "rate",
                "gst_rate": "gst_rate",
                "cgst": "cgst",
                "sgst": "sgst",
                "igst": "igst",
                "remarks": "remarks",
            },
            cgst_ledger=self._cgst_ledger.get(),
            sgst_ledger=self._sgst_ledger.get(),
            igst_ledger=self._igst_ledger.get(),
            round_off_ledger=self._round_off_ledger.get(),
        )

        if not valid:
            messagebox.showwarning(
                "Export", "Invoice validation failed.\nCheck validation messages."
            )
            return

        if val_errors:
            detail = build_error_detail(val_errors)
            proceed = messagebox.askyesno(
                "Validation Warnings",
                f"Some items have errors and will be skipped:\n\n"
                f"{detail}\n\n"
                f"Export the valid items?",
            )
            if not proceed:
                return

        path = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("XML Files", "*.xml"), ("All Files", "*.*")],
            title="Save Sales Itemwise Invoice XML",
        )
        if not path:
            return

        try:
            xml_content = build_sales_itemwise_xml(valid)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                fh.write(xml_content)
            messagebox.showinfo(
                "Export Complete",
                f"Exported {len(valid)} invoice(s) with {sum(len(inv.line_items) for inv in valid)} items to:\n{path}",
            )
            self._log(f"✅ Successfully exported invoice to {path}")
        except Exception as exc:
            messagebox.showerror("Export Error", str(exc))

    def _log(self, message: str) -> None:
        """Update status/log message."""
        self._status_text.configure(state="normal")
        self._status_text.delete("1.0", "end")
        self._status_text.insert("end", message)
        self._status_text.configure(state="disabled")
