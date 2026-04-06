"""XML generation for sales vouchers."""
from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET

from tally_importer.models import SalesEntry


def _sub(parent: ET.Element, tag: str, text: str = "") -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = text
    return el


def _indent(elem: ET.Element, level: int = 0) -> None:
    indent = "\n" + "  " * level
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
        for child in elem:
            _indent(child, level + 1)
        if not child.tail or not child.tail.strip():  # type: ignore[union-attr]
            child.tail = indent  # type: ignore[union-attr]
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent
    if not level:
        elem.tail = "\n"


def build_sales_xml(entries: list[SalesEntry]) -> str:
    """Generate Tally Prime-compatible XML for sales vouchers.

    Accounting entries per invoice:
    - Party (debtor) Dr  → ISDEEMEDPOSITIVE=Yes, amount = -total
    - Sales Ledger   Cr  → ISDEEMEDPOSITIVE=No,  amount = taxable
    - CGST Payable   Cr  → ISDEEMEDPOSITIVE=No,  amount = cgst  (if > 0)
    - SGST Payable   Cr  → ISDEEMEDPOSITIVE=No,  amount = sgst  (if > 0)
    - IGST Payable   Cr  → ISDEEMEDPOSITIVE=No,  amount = igst  (if > 0)
    - Round Off      Cr/Dr depending on sign
    """
    envelope = ET.Element("ENVELOPE")
    header = _sub(envelope, "HEADER")
    _sub(header, "TALLYREQUEST", "Import Data")

    body = _sub(envelope, "BODY")
    importdata = _sub(body, "IMPORTDATA")

    req_desc = _sub(importdata, "REQUESTDESC")
    _sub(req_desc, "REPORTNAME", "Vouchers")
    static_vars = _sub(req_desc, "STATICVARIABLES")
    _sub(static_vars, "SVCURRENTCOMPANY", "##SVCurrentCompany")

    req_data = _sub(importdata, "REQUESTDATA")

    for entry in entries:
        msg = _sub(req_data, "TALLYMESSAGE")
        msg.set("xmlns:UDF", "TallyUDF")

        voucher = _sub(msg, "VOUCHER")
        voucher.set("REMOTEID", str(uuid.uuid4()))
        voucher.set("VCHTYPE", entry.voucher_type)
        voucher.set("ACTION", "Create")
        voucher.set("OBJVIEW", "Invoice Voucher View")

        _sub(voucher, "DATE", entry.entry_date)
        _sub(voucher, "REFERENCEDATE", entry.original_date)
        _sub(voucher, "REFERENCE", entry.invoice_number)
        _sub(voucher, "NARRATION", entry.narration)
        _sub(voucher, "VOUCHERTYPENAME", entry.voucher_type)
        _sub(voucher, "VOUCHERNUMBER", entry.invoice_number)
        _sub(voucher, "PARTYLEDGERNAME", entry.party_name)

        total = round(entry.total_amount, 2)

        # Party Dr (debit)
        party_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
        _sub(party_entry, "LEDGERNAME", entry.party_name)
        _sub(party_entry, "ISDEEMEDPOSITIVE", "Yes")
        _sub(party_entry, "AMOUNT", str(-total))

        # Sales Cr
        sales_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
        _sub(sales_entry, "LEDGERNAME", entry.sales_ledger)
        _sub(sales_entry, "ISDEEMEDPOSITIVE", "No")
        _sub(sales_entry, "AMOUNT", str(round(entry.taxable_amount, 2)))

        # GST entries
        if entry.cgst:
            cgst_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
            _sub(cgst_entry, "LEDGERNAME", entry.cgst_ledger or "Output CGST")
            _sub(cgst_entry, "ISDEEMEDPOSITIVE", "No")
            _sub(cgst_entry, "AMOUNT", str(round(entry.cgst, 2)))

        if entry.sgst:
            sgst_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
            _sub(sgst_entry, "LEDGERNAME", entry.sgst_ledger or "Output SGST")
            _sub(sgst_entry, "ISDEEMEDPOSITIVE", "No")
            _sub(sgst_entry, "AMOUNT", str(round(entry.sgst, 2)))

        if entry.igst:
            igst_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
            _sub(igst_entry, "LEDGERNAME", entry.igst_ledger or "Output IGST")
            _sub(igst_entry, "ISDEEMEDPOSITIVE", "No")
            _sub(igst_entry, "AMOUNT", str(round(entry.igst, 2)))

        if entry.round_off:
            ro_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
            _sub(ro_entry, "LEDGERNAME", entry.round_off_ledger or "Round Off")
            is_debit = entry.round_off < 0
            _sub(ro_entry, "ISDEEMEDPOSITIVE", "Yes" if is_debit else "No")
            _sub(ro_entry, "AMOUNT", str(round(entry.round_off, 2)))

        if entry.gst_number:
            buyer = _sub(voucher, "BASICBUYERADDRESS.LIST")
            _sub(buyer, "BASICBUYERADDRESS", entry.gst_number)

    _indent(envelope)
    return ET.tostring(envelope, encoding="unicode", xml_declaration=False)
