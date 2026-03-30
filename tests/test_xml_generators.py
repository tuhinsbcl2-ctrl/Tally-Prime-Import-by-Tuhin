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

    # Bank Dr
    bank_entry = entries[0]
    assert bank_entry.find("LEDGERNAME").text == "HDFC Bank"
    assert bank_entry.find("ISDEEMEDPOSITIVE").text == "Yes"
    assert float(bank_entry.find("AMOUNT").text) == -5000.0

    # Party Cr
    party_entry = entries[1]
    assert party_entry.find("LEDGERNAME").text == "ABC Ltd"
    assert party_entry.find("ISDEEMEDPOSITIVE").text == "No"
    assert float(party_entry.find("AMOUNT").text) == 5000.0


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
    assert root.find(".//PARTYLEDGERNAME").text == "ABC Corp"

    entries = root.findall(".//ALLLEDGERENTRIES.LIST")
    # Party Dr, Sales Cr, CGST Cr, SGST Cr
    assert len(entries) == 4

    # Party Dr
    assert entries[0].find("LEDGERNAME").text == "ABC Corp"
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
    entries = root.findall(".//ALLLEDGERENTRIES.LIST")
    ledger_names = [e.find("LEDGERNAME").text for e in entries]
    assert "IGST" in ledger_names
    assert "CGST" not in ledger_names
    assert "SGST" not in ledger_names


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

    entries = root.findall(".//ALLLEDGERENTRIES.LIST")
    # Purchase Dr, CGST Dr, SGST Dr, Supplier Cr
    assert len(entries) == 4

    ledger_names = [e.find("LEDGERNAME").text for e in entries]
    assert "Purchase @18%" in ledger_names
    assert "CGST Input" in ledger_names
    assert "SGST Input" in ledger_names
    assert "Supplier A" in ledger_names

    # Supplier Cr
    supplier_entry = next(e for e in entries if e.find("LEDGERNAME").text == "Supplier A")
    assert supplier_entry.find("ISDEEMEDPOSITIVE").text == "No"
    assert float(supplier_entry.find("AMOUNT").text) == 17700.0
