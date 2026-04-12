"""Tests for XML generators."""
import xml.etree.ElementTree as ET
import pytest

from tally_importer.models import BankTransaction, SalesEntry, PurchaseEntry
from tally_importer.xml_generator import build_bank_xml, build_sales_xml, build_purchase_xml


# --- Bank XML ---

def test_bank_xml_structure():
    txn = BankTransaction(
        date="20240401", voucher_type="Receipt",
        bank_ledger="HDFC Bank", party_ledger="ABC Ltd",
        amount=5000.0, narration="Test receipt",
        transaction_id="T001", voucher_number="R001",
    )
    xml_str = build_bank_xml([txn])
    root = ET.fromstring(xml_str)

    assert root.tag == "ENVELOPE"
    voucher = root.find(".//VOUCHER")
    assert voucher is not None
    assert voucher.get("VCHTYPE") == "Receipt"
    assert root.find(".//DATE").text == "20240401"
    assert root.find(".//VOUCHERTYPENAME").text == "Receipt"

    entries = root.findall(".//ALLLEDGERENTRIES.LIST")
    assert len(entries) == 2

    # Bank Dr (first entry for Receipt)
    bank_entry = entries[0]
    assert bank_entry.find("LEDGERNAME").text == "HDFC Bank"
    assert bank_entry.find("ISDEEMEDPOSITIVE").text == "Yes"
    assert float(bank_entry.find("AMOUNT").text) == -5000.0

    # Bank entry always has BANKALLOCATIONS.LIST
    alloc = bank_entry.find("BANKALLOCATIONS.LIST")
    assert alloc is not None
    assert alloc.find("TRANSACTIONTYPE").text == "Others"

    # Party Cr
    party_entry = entries[1]
    assert party_entry.find("LEDGERNAME").text == "ABC Ltd"
    assert party_entry.find("ISDEEMEDPOSITIVE").text == "No"
    assert float(party_entry.find("AMOUNT").text) == 5000.0
    # Party entry must NOT have BANKALLOCATIONS.LIST
    assert party_entry.find("BANKALLOCATIONS.LIST") is None


def test_bank_xml_bank_allocations_with_inst_fields():
    """BANKALLOCATIONS.LIST must carry inst_no, inst_date and transaction_type."""
    txn = BankTransaction(
        date="20260331", voucher_type="Payment",
        bank_ledger="ICICI Bank", party_ledger="Vendor X",
        amount=29.50, inst_no="REF12345", inst_date="20260331",
        transaction_type="e-Fund Transfer",
    )
    xml_str = build_bank_xml([txn])
    root = ET.fromstring(xml_str)
    entries = root.findall(".//ALLLEDGERENTRIES.LIST")
    # Payment: Party Dr (no alloc), Bank Cr (has alloc)
    bank_entry = entries[1]
    assert bank_entry.find("LEDGERNAME").text == "ICICI Bank"
    alloc = bank_entry.find("BANKALLOCATIONS.LIST")
    assert alloc is not None
    assert alloc.find("INSTRUMENTNUMBER").text == "REF12345"
    assert alloc.find("INSTRUMENTDATE").text == "20260331"
    assert alloc.find("TRANSACTIONTYPE").text == "e-Fund Transfer"
    assert float(alloc.find("AMOUNT").text) == 29.50  # Cr → positive


def test_bank_xml_payment():
    txn = BankTransaction(
        date="20240402", voucher_type="Payment",
        bank_ledger="HDFC Bank", party_ledger="XYZ Supplier",
        amount=10000.0,
    )
    xml_str = build_bank_xml([txn])
    root = ET.fromstring(xml_str)
    entries = root.findall(".//ALLLEDGERENTRIES.LIST")
    # Payment: Party Dr, Bank Cr
    assert entries[0].find("LEDGERNAME").text == "XYZ Supplier"
    assert entries[0].find("ISDEEMEDPOSITIVE").text == "Yes"
    assert entries[1].find("LEDGERNAME").text == "HDFC Bank"
    assert entries[1].find("ISDEEMEDPOSITIVE").text == "No"


def test_bank_xml_multiple():
    txns = [
        BankTransaction("20240401", "Receipt", "Bank A", "Party A", 1000.0),
        BankTransaction("20240402", "Payment", "Bank B", "Party B", 2000.0),
    ]
    xml_str = build_bank_xml(txns)
    root = ET.fromstring(xml_str)
    vouchers = root.findall(".//VOUCHER")
    assert len(vouchers) == 2


# --- Sales XML ---

def test_sales_xml_structure():
    entry = SalesEntry(
        party_name="ABC Corp", invoice_number="INV-001",
        entry_date="20240401", original_date="20240401",
        sales_ledger="Sales @18%", taxable_amount=10000.0,
        cgst=900.0, sgst=900.0, igst=0.0, total_amount=11800.0,
    )
    xml_str = build_sales_xml([entry])
    root = ET.fromstring(xml_str)

    voucher = root.find(".//VOUCHER")
    assert voucher.get("VCHTYPE") == "Sales"
    assert voucher.get("OBJVIEW") == "Invoice Voucher View"
    assert root.find(".//ISINVOICE").text == "Yes"
    assert root.find(".//PERSISTEDVIEW").text == "Invoice Voucher View"
    assert root.find(".//EFFECTIVEDATE").text == "20240401"
    assert root.find(".//PARTYLEDGERNAME").text == "ABC Corp"

    entries = root.findall(".//LEDGERENTRIES.LIST")
    # Party Dr, Sales Cr, CGST Cr, SGST Cr
    assert len(entries) == 4

    # Party Dr (must be first, with ISPARTYLEDGER)
    assert entries[0].find("LEDGERNAME").text == "ABC Corp"
    assert entries[0].find("ISPARTYLEDGER").text == "Yes"
    assert entries[0].find("ISDEEMEDPOSITIVE").text == "Yes"
    assert float(entries[0].find("AMOUNT").text) == -11800.0

    # Sales Cr
    assert entries[1].find("LEDGERNAME").text == "Sales @18%"
    assert float(entries[1].find("AMOUNT").text) == 10000.0


def test_sales_xml_igst():
    entry = SalesEntry(
        party_name="Inter State Co", invoice_number="INV-002",
        entry_date="20240401", original_date="20240401",
        sales_ledger="Sales @18%", taxable_amount=10000.0,
        cgst=0.0, sgst=0.0, igst=1800.0, total_amount=11800.0,
    )
    xml_str = build_sales_xml([entry])
    root = ET.fromstring(xml_str)
    entries = root.findall(".//LEDGERENTRIES.LIST")
    ledger_names = [e.find("LEDGERNAME").text for e in entries]
    assert "Output IGST" in ledger_names
    assert "Output CGST" not in ledger_names
    assert "Output SGST" not in ledger_names


# --- Purchase XML ---

def test_purchase_xml_structure():
    entry = PurchaseEntry(
        party_name="Supplier A", invoice_number="SUP-001",
        entry_date="20240405", original_date="20240404",
        purchase_ledger="Purchase @18%", taxable_amount=15000.0,
        cgst=1350.0, sgst=1350.0, igst=0.0, total_amount=17700.0,
    )
    xml_str = build_purchase_xml([entry])
    root = ET.fromstring(xml_str)

    voucher = root.find(".//VOUCHER")
    assert voucher.get("VCHTYPE") == "Purchase"
    assert voucher.get("OBJVIEW") == "Invoice Voucher View"
    assert root.find(".//ISINVOICE").text == "Yes"
    assert root.find(".//PERSISTEDVIEW").text == "Invoice Voucher View"
    assert root.find(".//EFFECTIVEDATE").text == "20240405"

    entries = root.findall(".//LEDGERENTRIES.LIST")
    # Supplier Cr (first), Purchase Dr, CGST Dr, SGST Dr
    assert len(entries) == 4

    ledger_names = [e.find("LEDGERNAME").text for e in entries]
    assert "Purchase @18%" in ledger_names
    assert "Input CGST" in ledger_names
    assert "Input SGST" in ledger_names
    assert "Supplier A" in ledger_names

    # Supplier Cr must be first with ISPARTYLEDGER=Yes
    assert entries[0].find("LEDGERNAME").text == "Supplier A"
    assert entries[0].find("ISPARTYLEDGER").text == "Yes"
    assert entries[0].find("ISDEEMEDPOSITIVE").text == "No"
    assert float(entries[0].find("AMOUNT").text) == 17700.0
