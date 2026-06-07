"""XML generation for purchase itemwise vouchers."""
from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET

from tally_importer.models import PurchaseItemwise
from tally_importer.xml_generator._helpers import _indent, _sub


def build_purchase_itemwise_xml(invoices: list[PurchaseItemwise]) -> str:
    """Generate Tally Prime-compatible XML for itemwise purchase vouchers."""
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

    for invoice in invoices:
        msg = _sub(req_data, "TALLYMESSAGE")
        msg.set("xmlns:UDF", "TallyUDF")

        voucher = _sub(msg, "VOUCHER")
        voucher.set("REMOTEID", str(uuid.uuid4()))
        voucher.set("VCHTYPE", invoice.voucher_type)
        voucher.set("ACTION", "Create")
        voucher.set("OBJVIEW", "Invoice Voucher View")

        _sub(voucher, "DATE", invoice.entry_date)
        _sub(voucher, "EFFECTIVEDATE", invoice.entry_date)
        _sub(voucher, "ISINVOICE", "Yes")
        _sub(voucher, "PERSISTEDVIEW", "Invoice Voucher View")
        _sub(voucher, "VCHENTRYMODE", "Accounting Invoice")
        _sub(voucher, "REFERENCEDATE", invoice.original_date)
        _sub(voucher, "REFERENCE", invoice.invoice_number)
        _sub(voucher, "NARRATION", invoice.narration)
        _sub(voucher, "VOUCHERTYPENAME", invoice.voucher_type)
        _sub(voucher, "VOUCHERNUMBER", invoice.invoice_number)
        _sub(voucher, "PARTYLEDGERNAME", invoice.party_name)

        total = round(invoice.total_amount, 2)

        # Party Cr (party ledger)
        party_entry = _sub(voucher, "LEDGERENTRIES.LIST")
        _sub(party_entry, "LEDGERNAME", invoice.party_name)
        _sub(party_entry, "ISPARTYLEDGER", "Yes")
        _sub(party_entry, "ISDEEMEDPOSITIVE", "No")
        _sub(party_entry, "AMOUNT", str(total))

        # Purchase Dr
        purchase_entry = _sub(voucher, "LEDGERENTRIES.LIST")
        _sub(purchase_entry, "LEDGERNAME", invoice.purchase_ledger)
        _sub(purchase_entry, "ISDEEMEDPOSITIVE", "Yes")
        _sub(purchase_entry, "AMOUNT", str(round(invoice.total_taxable, 2)))

        # GST entries
        if invoice.total_cgst:
            cgst_entry = _sub(voucher, "LEDGERENTRIES.LIST")
            _sub(cgst_entry, "LEDGERNAME", invoice.cgst_ledger or "Input CGST")
            _sub(cgst_entry, "ISDEEMEDPOSITIVE", "Yes")
            _sub(cgst_entry, "AMOUNT", str(round(invoice.total_cgst, 2)))

        if invoice.total_sgst:
            sgst_entry = _sub(voucher, "LEDGERENTRIES.LIST")
            _sub(sgst_entry, "LEDGERNAME", invoice.sgst_ledger or "Input SGST")
            _sub(sgst_entry, "ISDEEMEDPOSITIVE", "Yes")
            _sub(sgst_entry, "AMOUNT", str(round(invoice.total_sgst, 2)))

        if invoice.total_igst:
            igst_entry = _sub(voucher, "LEDGERENTRIES.LIST")
            _sub(igst_entry, "LEDGERNAME", invoice.igst_ledger or "Input IGST")
            _sub(igst_entry, "ISDEEMEDPOSITIVE", "Yes")
            _sub(igst_entry, "AMOUNT", str(round(invoice.total_igst, 2)))

        # Item details (lineitem list)
        for item in invoice.line_items:
            line_item = _sub(voucher, "LINEITEM.LIST")
            _sub(line_item, "LINENO", "1")
            _sub(line_item, "ITEMNAME", item.item_name)
            _sub(line_item, "HSNCODE", item.hsn_code)
            _sub(line_item, "UQC", item.unit)
            _sub(line_item, "QUANTITY", str(round(item.qty, 2)))
            _sub(line_item, "RATE", str(round(item.rate, 2)))
            _sub(line_item, "AMOUNT", str(round(item.amount, 2)))
            if item.remarks:
                _sub(line_item, "DESCRIPTION", item.remarks)

        if invoice.gst_number:
            buyer = _sub(voucher, "BASICBUYERADDRESS.LIST")
            _sub(buyer, "BASICBUYERADDRESS", invoice.gst_number)

        if invoice.place_of_supply:
            _sub(voucher, "PLACEOFSUPPLY", invoice.place_of_supply)

    _indent(envelope)
    return ET.tostring(envelope, encoding="unicode", xml_declaration=False)
