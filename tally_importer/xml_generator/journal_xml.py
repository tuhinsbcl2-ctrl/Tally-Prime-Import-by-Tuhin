"""XML generation for journal entries."""
from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET

from tally_importer.models import JournalEntry
from tally_importer.xml_generator._helpers import _indent, _sub


def build_journal_xml(entries: list[JournalEntry]) -> str:
    """Generate Tally Prime-compatible XML for journal entries."""
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
        voucher.set("VCHTYPE", "Journal")
        voucher.set("ACTION", "Create")
        voucher.set("OBJVIEW", "Accounting Voucher View")

        _sub(voucher, "DATE", entry.date)
        _sub(voucher, "EFFECTIVEDATE", entry.date)
        _sub(voucher, "NARRATION", entry.narration)
        _sub(voucher, "VOUCHERTYPENAME", "Journal")
        
        if entry.reference_number:
            _sub(voucher, "VOUCHERNUMBER", entry.reference_number)
        if entry.invoice_number:
            _sub(voucher, "REFERENCE", entry.invoice_number)

        # Debit entry
        debit_entry = _sub(voucher, "LEDGERENTRIES.LIST")
        _sub(debit_entry, "LEDGERNAME", entry.debit_ledger)
        _sub(debit_entry, "ISDEEMEDPOSITIVE", "Yes")
        _sub(debit_entry, "AMOUNT", str(round(entry.debit_amount, 2)))

        # Credit entry
        credit_entry = _sub(voucher, "LEDGERENTRIES.LIST")
        _sub(credit_entry, "LEDGERNAME", entry.credit_ledger)
        _sub(credit_entry, "ISDEEMEDPOSITIVE", "No")
        _sub(credit_entry, "AMOUNT", str(round(entry.credit_amount, 2)))

    _indent(envelope)
    return ET.tostring(envelope, encoding="unicode", xml_declaration=False)
