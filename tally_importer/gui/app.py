"""Main application window."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from tally_importer.gui.bank_tab import BankTab
from tally_importer.gui.debit_credit_tab import DebitCreditTab
from tally_importer.gui.journal_tab import JournalTab
from tally_importer.gui.purchase_itemwise_tab import PurchaseItemwiseTab
from tally_importer.gui.purchase_tab import PurchaseTab
from tally_importer.gui.sales_itemwise_tab import SalesItemwiseTab
from tally_importer.gui.sales_tab import SalesTab


class App(tk.Tk):
    """Root window of the Tally Prime Importer application."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Tally Prime Importer – by Tuhin (Enhanced)")
        self.geometry("1200x750")
        self.minsize(900, 600)

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
        notebook.add(sales_tab, text="  Sales (Services)  ")

        sales_itemwise_tab = SalesItemwiseTab(notebook)
        notebook.add(sales_itemwise_tab, text="  Sales Itemwise  ")

        purchase_tab = PurchaseTab(notebook)
        notebook.add(purchase_tab, text="  Purchase (Services)  ")

        purchase_itemwise_tab = PurchaseItemwiseTab(notebook)
        notebook.add(purchase_itemwise_tab, text="  Purchase Itemwise  ")

        debit_credit_tab = DebitCreditTab(notebook)
        notebook.add(debit_credit_tab, text="  Debit/Credit Notes  ")

        journal_tab = JournalTab(notebook)
        notebook.add(journal_tab, text="  Journal Entries  ")

    def _show_about(self) -> None:
        from tkinter import messagebox

        messagebox.showinfo(
            "About",
            "Tally Prime Importer (Enhanced)"
            "\nVersion 2.0\n\n"
            "Import Excel data and export Tally Prime-compatible XML vouchers.\n\n"
            "Supports:\n"
            "  • Bank Vouchers (Receipt / Payment / Contra)\n"
            "  • Sales Vouchers (Services)\n"
            "  • Sales Itemwise Invoices\n"
            "  • Purchase Vouchers (Services)\n"
            "  • Purchase Itemwise Invoices\n"
            "  • Debit Note / Credit Note Vouchers\n"
            "  • Journal Entries\n\n"
            "With address tracking (Billing/Shipping) and full item-level details.\n\n"
            "Built with Python + tkinter.",
        )
