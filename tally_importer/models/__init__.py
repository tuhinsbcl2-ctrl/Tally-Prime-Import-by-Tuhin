"""Data models for bank transactions, sales and purchase entries."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BankTransaction:
    """Represents a single bank transaction row (Receipt / Payment / Contra)."""

    date: str                   # YYYYMMDD string expected for Tally
    voucher_type: str           # 'Receipt' | 'Payment' | 'Contra'
    bank_ledger: str            # Bank / payment mode ledger name
    party_ledger: str           # Counter-party ledger name
    amount: float               # Positive amount
    narration: str = ""
    transaction_id: str = ""
    voucher_number: str = ""


@dataclass
class SalesEntry:
    """Represents a single sales invoice row."""

    party_name: str
    invoice_number: str
    entry_date: str             # YYYYMMDD
    original_date: str          # YYYYMMDD
    sales_ledger: str
    taxable_amount: float
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    gst_rate: float = 0.0
    round_off: float = 0.0
    total_amount: float = 0.0
    gst_number: str = ""
    narration: str = ""


@dataclass
class PurchaseEntry:
    """Represents a single purchase invoice row."""

    party_name: str
    invoice_number: str
    entry_date: str             # YYYYMMDD
    original_date: str          # YYYYMMDD
    purchase_ledger: str
    taxable_amount: float
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    gst_rate: float = 0.0
    round_off: float = 0.0
    total_amount: float = 0.0
    gst_number: str = ""
    narration: str = ""
