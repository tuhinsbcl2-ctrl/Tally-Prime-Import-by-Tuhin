"""Reusable column-mapping dialog.

Opens a modal window where the user can select which Excel column maps
to each required/optional Tally field.  Mapping can be saved/loaded as
named templates.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from tally_importer import mapping as mapping_store


class MappingDialog(tk.Toplevel):
    """Modal dialog for column→field mapping."""

    def __init__(
        self,
        parent: tk.Widget,
        voucher_type: str,
        fields: list[tuple[str, str, bool]],
        excel_columns: list[str],
        current_mapping: dict[str, str] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(f"Column Mapping – {voucher_type}")
        self.resizable(True, True)
        self.grab_set()

        self._voucher_type = voucher_type
        self._fields = fields
        self._excel_columns = ["(not mapped)"] + excel_columns
        self._vars: dict[str, tk.StringVar] = {}
        self.result: dict[str, str] | None = None

        self._build_ui(current_mapping or {})
        self.update_idletasks()
        self.minsize(520, 400)
        self._center()

    # ------------------------------------------------------------------
    def _build_ui(self, current: dict[str, str]) -> None:
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # Template row
        tmpl_frame = ttk.LabelFrame(main, text="Templates", padding=6)
        tmpl_frame.pack(fill="x", pady=(0, 8))

        self._tmpl_var = tk.StringVar()
        templates = mapping_store.list_templates(self._voucher_type)
        self._tmpl_combo = ttk.Combobox(
            tmpl_frame, textvariable=self._tmpl_var, values=templates, width=22
        )
        self._tmpl_combo.pack(side="left", padx=(0, 4))

        ttk.Button(tmpl_frame, text="Load", command=self._load_template).pack(
            side="left", padx=2
        )
        ttk.Button(tmpl_frame, text="Save As…", command=self._save_template).pack(
            side="left", padx=2
        )

        # Scrollable mapping area
        canvas = tk.Canvas(main, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_configure(event: Any) -> None:  # noqa: ANN001
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=event.width)

        inner.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_configure)

        # Header
        ttk.Label(inner, text="Tally Field", font=("", 9, "bold")).grid(
            row=0, column=0, sticky="w", padx=4, pady=2
        )
        ttk.Label(inner, text="Excel Column", font=("", 9, "bold")).grid(
            row=0, column=1, sticky="w", padx=4, pady=2
        )
        ttk.Label(inner, text="Req.", font=("", 9, "bold")).grid(
            row=0, column=2, sticky="w", padx=4, pady=2
        )
        ttk.Separator(inner, orient="horizontal").grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=4
        )

        for i, (key, label, required) in enumerate(self._fields, start=2):
            req_mark = "✱" if required else ""
            ttk.Label(inner, text=f"{label}  {req_mark}").grid(
                row=i, column=0, sticky="w", padx=4, pady=3
            )
            var = tk.StringVar(value=current.get(key, "(not mapped)"))
            self._vars[key] = var
            cb = ttk.Combobox(
                inner,
                textvariable=var,
                values=self._excel_columns,
                state="readonly",
                width=28,
            )
            cb.grid(row=i, column=1, sticky="ew", padx=4, pady=3)

        inner.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", pady=6, padx=10)
        ttk.Button(btn_frame, text="OK", command=self._ok, width=10).pack(
            side="right", padx=4
        )
        ttk.Button(btn_frame, text="Cancel", command=self.destroy, width=10).pack(
            side="right"
        )

    # ------------------------------------------------------------------
    def _ok(self) -> None:
        mapping = {
            key: var.get()
            for key, var in self._vars.items()
            if var.get() != "(not mapped)"
        }
        self.result = mapping
        self.destroy()

    def _load_template(self) -> None:
        name = self._tmpl_var.get().strip()
        if not name:
            messagebox.showwarning("Load Template", "Enter a template name.", parent=self)
            return
        tmpl = mapping_store.load_template(self._voucher_type, name)
        if not tmpl:
            messagebox.showwarning(
                "Load Template", f"Template '{name}' not found.", parent=self
            )
            return
        for key, var in self._vars.items():
            value = tmpl.get(key, "(not mapped)")
            if value in self._excel_columns:
                var.set(value)
            else:
                var.set("(not mapped)")

    def _save_template(self) -> None:
        name = self._tmpl_var.get().strip()
        if not name:
            name = tk.simpledialog.askstring(  # type: ignore[attr-defined]
                "Save Template", "Template name:", parent=self
            )
        if not name:
            return
        mapping = {
            key: var.get()
            for key, var in self._vars.items()
            if var.get() != "(not mapped)"
        }
        mapping_store.save_template(self._voucher_type, name, mapping)
        templates = mapping_store.list_templates(self._voucher_type)
        self._tmpl_combo.configure(values=templates)
        messagebox.showinfo(
            "Save Template", f"Template '{name}' saved.", parent=self
        )

    def _center(self) -> None:
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"+{x}+{y}")
