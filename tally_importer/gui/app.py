"""Main application window."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from tally_importer.gui.bank_tab import BankTab
from tally_importer.gui.debit_credit_tab import DebitCreditTab
from tally_importer.gui.sales_tab import SalesTab
from tally_importer.gui.purchase_tab import PurchaseTab


class App(tk.Tk):
    """Root window of the Tally Prime Importer application."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Tally Prime Importer – by Tuhin")
        self.geometry("1000x700")
        self.minsize(800, 550)

        self._build_menu()
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_ui(self) -> None:
        # Status bar at the bottom
        status_bar = ttk.Label(
            self,
            text="Ready – load an Excel file to begin.",
            relief="sunken",
            anchor="w",
            padding=(4, 2),
        )
        status_bar.pack(side="bottom", fill="x")

        # Notebook tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=4, pady=4)

        bank_tab = BankTab(notebook)
        notebook.add(bank_tab, text="  Bank Vouchers  ")

        sales_tab = SalesTab(notebook)
        notebook.add(sales_tab, text="  Sales  ")

        purchase_tab = PurchaseTab(notebook)
        notebook.add(purchase_tab, text="  Purchase  ")

        debit_credit_tab = DebitCreditTab(notebook)
        notebook.add(debit_credit_tab, text="  Debit/Credit Notes  ")

    def _show_about(self) -> None:
        from tkinter import messagebox

        messagebox.showinfo(
            "About",
            "Tally Prime Importer\n"
            "Version 1.0 (MVP)\n\n"
            "Import Excel data and export Tally Prime-compatible XML vouchers.\n\n"
            "Supports:\n"
            "  • Bank Vouchers (Receipt / Payment / Contra)\n"
            "  • Sales Vouchers\n"
            "  • Purchase Vouchers\n"
            "  • Debit Note / Credit Note Vouchers\n\n"
            "Built with Python + tkinter.",
        )
