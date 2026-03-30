"""Tests for the validator module."""
import pytest
from tally_importer.validator import validate_bank_transactions, validate_sales, validate_purchase, _normalize_date


# --- Date normalization ---

def test_normalize_date_yyyymmdd():
    assert _normalize_date("20240101") == "20240101"

def test_normalize_date_dd_mm_yyyy():
    assert _normalize_date("01-04-2024") == "20240401"

def test_normalize_date_slash():
    assert _normalize_date("15/06/2023") == "20230615"

def test_normalize_date_iso():
    assert _normalize_date("2024-03-25") == "20240325"


# --- Bank validation ---

BANK_MAPPING = {
    "date": "Date",
    "voucher_type": "Voucher Type",
    "bank_ledger": "Bank",
    "party_ledger": "Party",
    "amount": "Amount",
    "narration": "Narration",
    "transaction_id": "TxnID",
    "voucher_number": "VchNo",
}

def _bank_row(**kw):
    base = {
        "Date": "01-04-2024", "Voucher Type": "Receipt",
        "Bank": "HDFC Bank", "Party": "ABC Ltd",
        "Amount": "5000", "Narration": "Test", "TxnID": "T001", "VchNo": "R001",
    }
    base.update(kw)
    return base


def test_bank_valid_row():
    valid, errors = validate_bank_transactions([_bank_row()], BANK_MAPPING)
    assert len(valid) == 1
    assert len(errors) == 0
    assert valid[0].voucher_type == "Receipt"
    assert valid[0].amount == 5000.0
    assert valid[0].date == "20240401"


def test_bank_missing_date():
    _, errors = validate_bank_transactions([_bank_row(Date="")], BANK_MAPPING)
    assert any("date" in e["errors"][0].lower() for e in errors)


def test_bank_invalid_voucher_type():
    _, errors = validate_bank_transactions(
        [_bank_row(**{"Voucher Type": "Unknown"})], BANK_MAPPING
    )
    assert any("voucher type" in e["errors"][0].lower() for e in errors)


def test_bank_default_voucher_type():
    row = _bank_row()
    del row["Voucher Type"]
    mapping = {k: v for k, v in BANK_MAPPING.items() if k != "voucher_type"}
    valid, errors = validate_bank_transactions([row], mapping, default_voucher_type="Payment")
    assert len(valid) == 1
    assert valid[0].voucher_type == "Payment"


def test_bank_invalid_amount():
    _, errors = validate_bank_transactions([_bank_row(Amount="abc")], BANK_MAPPING)
    assert any("amount" in e["errors"][0].lower() for e in errors)


def test_bank_zero_amount():
    _, errors = validate_bank_transactions([_bank_row(Amount="0")], BANK_MAPPING)
    assert any("amount" in e["errors"][0].lower() for e in errors)


# --- Sales validation ---

SALES_MAPPING = {
    "party_name": "Party", "invoice_number": "Invoice", "entry_date": "Date",
    "original_date": "Orig Date", "sales_ledger": "Ledger",
    "taxable_amount": "Taxable", "cgst": "CGST", "sgst": "SGST",
    "igst": "IGST", "gst_rate": "Rate", "round_off": "RO",
    "total_amount": "Total", "gst_number": "GST", "narration": "Narr",
}

def _sales_row(**kw):
    base = {
        "Party": "ABC Corp", "Invoice": "INV-001", "Date": "01-04-2024",
        "Orig Date": "01-04-2024", "Ledger": "Sales @18%",
        "Taxable": "10000", "CGST": "900", "SGST": "900",
        "IGST": "0", "Rate": "18", "RO": "0", "Total": "11800",
        "GST": "29AABCA1234A1Z5", "Narr": "Sales",
    }
    base.update(kw)
    return base


def test_sales_valid():
    valid, errors = validate_sales([_sales_row()], SALES_MAPPING)
    assert len(valid) == 1
    assert valid[0].party_name == "ABC Corp"
    assert valid[0].taxable_amount == 10000.0


def test_sales_missing_invoice():
    _, errors = validate_sales([_sales_row(Invoice="")], SALES_MAPPING)
    assert any("invoice" in e["errors"][0].lower() for e in errors)


def test_sales_missing_party():
    _, errors = validate_sales([_sales_row(Party="")], SALES_MAPPING)
    assert any("party" in e["errors"][0].lower() for e in errors)


def test_sales_tax_mismatch():
    # 10000 + 900 + 900 = 11800 but we say total = 15000
    _, errors = validate_sales([_sales_row(Total="15000")], SALES_MAPPING)
    assert any("mismatch" in e["errors"][0].lower() for e in errors)


# --- Purchase validation ---

PURCHASE_MAPPING = {
    "party_name": "Party", "invoice_number": "Invoice", "entry_date": "Date",
    "original_date": "Orig Date", "purchase_ledger": "Ledger",
    "taxable_amount": "Taxable", "cgst": "CGST", "sgst": "SGST",
    "igst": "IGST", "gst_rate": "Rate", "round_off": "RO",
    "total_amount": "Total", "gst_number": "GST", "narration": "Narr",
}

def _purchase_row(**kw):
    base = {
        "Party": "Supplier A", "Invoice": "SUP-001", "Date": "05-04-2024",
        "Orig Date": "04-04-2024", "Ledger": "Purchase @18%",
        "Taxable": "15000", "CGST": "1350", "SGST": "1350",
        "IGST": "0", "Rate": "18", "RO": "0", "Total": "17700",
        "GST": "29AABCA9999A1Z5", "Narr": "Purchase",
    }
    base.update(kw)
    return base


def test_purchase_valid():
    valid, errors = validate_purchase([_purchase_row()], PURCHASE_MAPPING)
    assert len(valid) == 1
    assert valid[0].invoice_number == "SUP-001"


def test_purchase_missing_ledger():
    _, errors = validate_purchase([_purchase_row(Ledger="")], PURCHASE_MAPPING)
    assert any("ledger" in e["errors"][0].lower() for e in errors)
