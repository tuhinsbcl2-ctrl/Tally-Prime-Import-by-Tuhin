"""XML generation for purchase vouchers."""
from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET

from tally_importer.models import PurchaseEntry


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


def build_purchase_xml(entries: list[PurchaseEntry]) -> str:
    """Generate Tally Prime-compatible XML for purchase vouchers.

    Accounting entries per invoice:
    - Purchase Ledger Dr → ISDEEMEDPOSITIVE=Yes, amount = -taxable
    - CGST Input      Dr → ISDEEMEDPOSITIVE=Yes, amount = -cgst  (if > 0)
    - SGST Input      Dr → ISDEEMEDPOSITIVE=Yes, amount = -sgst  (if > 0)
    - IGST Input      Dr → ISDEEMEDPOSITIVE=Yes, amount = -igst  (if > 0)
    - Round Off       Dr/Cr depending on sign
    - Supplier (creditor) Cr → ISDEEMEDPOSITIVE=No, amount = total
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

        # Purchase Dr
        pur_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
        _sub(pur_entry, "LEDGERNAME", entry.purchase_ledger)
        _sub(pur_entry, "ISDEEMEDPOSITIVE", "Yes")
        _sub(pur_entry, "AMOUNT", str(-round(entry.taxable_amount, 2)))

        # GST input tax Dr
        if entry.cgst:
            cgst_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
            _sub(cgst_entry, "LEDGERNAME", "CGST Input")
            _sub(cgst_entry, "ISDEEMEDPOSITIVE", "Yes")
            _sub(cgst_entry, "AMOUNT", str(-round(entry.cgst, 2)))

        if entry.sgst:
            sgst_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
            _sub(sgst_entry, "LEDGERNAME", "SGST Input")
            _sub(sgst_entry, "ISDEEMEDPOSITIVE", "Yes")
            _sub(sgst_entry, "AMOUNT", str(-round(entry.sgst, 2)))

        if entry.igst:
            igst_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
            _sub(igst_entry, "LEDGERNAME", "IGST Input")
            _sub(igst_entry, "ISDEEMEDPOSITIVE", "Yes")
            _sub(igst_entry, "AMOUNT", str(-round(entry.igst, 2)))

        if entry.round_off:
            ro_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
            _sub(ro_entry, "LEDGERNAME", "Round Off")
            is_debit = entry.round_off > 0
            _sub(ro_entry, "ISDEEMEDPOSITIVE", "Yes" if is_debit else "No")
            _sub(ro_entry, "AMOUNT", str(round(entry.round_off, 2)))

        # Supplier Cr
        party_entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
        _sub(party_entry, "LEDGERNAME", entry.party_name)
        _sub(party_entry, "ISDEEMEDPOSITIVE", "No")
        _sub(party_entry, "AMOUNT", str(total))

    _indent(envelope)
    return ET.tostring(envelope, encoding="unicode", xml_declaration=False)
