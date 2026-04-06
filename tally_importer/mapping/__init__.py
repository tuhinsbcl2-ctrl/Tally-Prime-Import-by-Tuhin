"""Column mapping persistence.

Mappings are stored as JSON files in the user's home directory under
``~/.tally_importer/mappings/``.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_MAPPING_DIR = Path.home() / ".tally_importer" / "mappings"


def _ensure_dir() -> None:
    _MAPPING_DIR.mkdir(parents=True, exist_ok=True)


def list_templates(voucher_type: str) -> list[str]:
    """Return saved template names for the given voucher type."""
    _ensure_dir()
    prefix = f"{voucher_type}_"
    return [
        f.stem[len(prefix):]
        for f in _MAPPING_DIR.glob(f"{prefix}*.json")
    ]


def save_template(voucher_type: str, name: str, mapping: dict[str, str]) -> None:
    """Persist a mapping template to disk."""
    _ensure_dir()
    path = _MAPPING_DIR / f"{voucher_type}_{name}.json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(mapping, fh, indent=2)


def load_template(voucher_type: str, name: str) -> dict[str, str]:
    """Load a previously saved mapping template."""
    path = _MAPPING_DIR / f"{voucher_type}_{name}.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def delete_template(voucher_type: str, name: str) -> None:
    path = _MAPPING_DIR / f"{voucher_type}_{name}.json"
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# Field definitions used by the mapping UI
# ---------------------------------------------------------------------------

BANK_FIELDS: list[tuple[str, str, bool]] = [
    # (internal_key, label, required)
    ("date",           "Date",                True),
    ("bank_ledger",    "Bank / Payment Mode", True),
    ("party_ledger",   "Party Name / Ledger", True),
    ("amount",         "Amount",              True),
    ("voucher_type",   "Voucher Type",        False),
    ("narration",      "Narration",           False),
    ("transaction_id", "Transaction ID",      False),
    ("voucher_number", "Voucher Number",       False),
    ("inst_no",        "Instrument No.",       False),
    ("inst_date",      "Instrument Date",      False),
    ("transaction_type", "Transaction Type",   False),
]

SALES_FIELDS: list[tuple[str, str, bool]] = [
    ("party_name",     "Party Name",          True),
    ("invoice_number", "Invoice Number",      True),
    ("entry_date",     "Entry Date",          True),
    ("original_date",  "Original Date",       False),
    ("sales_ledger",   "Sales Ledger",        True),
    ("taxable_amount", "Taxable Amount",      True),
    ("gst_rate",       "GST Rate",           False),
    ("hsn_code",       "HSN/SAC Code",       False),
    ("cgst",           "CGST Amount",        False),
    ("sgst",           "SGST Amount",        False),
    ("igst",           "IGST Amount",        False),
    ("round_off",      "Round Off",          False),
    ("total_amount",   "Total Amount",       True),
    ("gst_number",     "GST Number",         False),
    ("narration",      "Narration",          False),
    ("voucher_type",   "Voucher Type",       True),
]

PURCHASE_FIELDS: list[tuple[str, str, bool]] = [
    ("party_name",     "Party Name",          True),
    ("invoice_number", "Invoice Number",      True),
    ("entry_date",     "Entry Date",          True),
    ("original_date",  "Original Date",       False),
    ("purchase_ledger","Purchase Ledger",     True),
    ("taxable_amount", "Taxable Amount",      True),
    ("cgst",           "CGST",               False),
    ("sgst",           "SGST",               False),
    ("igst",           "IGST",               False),
    ("gst_rate",       "GST Rate",           False),
    ("round_off",      "Round Off",          False),
    ("total_amount",   "Total Amount",       False),
    ("gst_number",     "GST Number",         False),
    ("narration",      "Narration",          False),
    ("voucher_type",   "Voucher Type",       False),
]
