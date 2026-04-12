"""XML generation for bank vouchers (Receipt / Payment / Contra)."""
from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET

from tally_importer.models import BankTransaction
from tally_importer.xml_generator._helpers import _indent, _sub


def build_bank_xml(transactions: list[BankTransaction]) -> str:
    """Generate Tally Prime-compatible XML for bank vouchers.

    Tally debit/credit convention:
    - Receipt  : bank account Dr (positive in Tally)  | party Cr (negative)
    - Payment  : party account Dr (positive)          | bank Cr (negative)
    - Contra   : bank-in Dr (positive)                | bank-out Cr (negative)

    Tally represents amounts as:
    - ISDEEMEDPOSITIVE=Yes  → debit  → amount stored as *negative* in XML
    - ISDEEMEDPOSITIVE=No   → credit → amount stored as *positive* in XML
    This counter-intuitive sign is how Tally's XML format works.
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

    for txn in transactions:
        msg = _sub(req_data, "TALLYMESSAGE")
        msg.set("xmlns:UDF", "TallyUDF")

        remote_id = txn.voucher_number or str(uuid.uuid4())
        voucher = _sub(msg, "VOUCHER")
        voucher.set("REMOTEID", remote_id)
        voucher.set("VCHTYPE", txn.voucher_type)
        voucher.set("ACTION", "Create")
        voucher.set("OBJVIEW", "Accounting Voucher View")

        _sub(voucher, "DATE", txn.date)
        _sub(voucher, "NARRATION", txn.narration)
        _sub(voucher, "VOUCHERTYPENAME", txn.voucher_type)
        _sub(voucher, "VOUCHERNUMBER", txn.voucher_number or "")
        if txn.transaction_id:
            _sub(voucher, "REFERENCEDATE", txn.date)
            _sub(voucher, "REFERENCE", txn.transaction_id)

        amount = txn.amount

        if txn.voucher_type == "Receipt":
            # Bank Dr, Party Cr
            _add_ledger_entry(voucher, txn.bank_ledger, is_debit=True,  amount=amount,
                              is_bank_entry=True, txn=txn)
            _add_ledger_entry(voucher, txn.party_ledger, is_debit=False, amount=amount)

        elif txn.voucher_type == "Payment":
            # Party Dr, Bank Cr
            _add_ledger_entry(voucher, txn.party_ledger, is_debit=True,  amount=amount)
            _add_ledger_entry(voucher, txn.bank_ledger,  is_debit=False, amount=amount,
                              is_bank_entry=True, txn=txn)

        else:  # Contra
            # bank-in Dr, bank-out Cr  (bank_ledger = destination, party_ledger = source)
            _add_ledger_entry(voucher, txn.bank_ledger,  is_debit=True,  amount=amount,
                              is_bank_entry=True, txn=txn)
            _add_ledger_entry(voucher, txn.party_ledger, is_debit=False, amount=amount)

    _indent(envelope)
    return ET.tostring(envelope, encoding="unicode", xml_declaration=False)


def _add_ledger_entry(
    voucher: ET.Element,
    ledger_name: str,
    is_debit: bool,
    amount: float,
    is_bank_entry: bool = False,
    txn: "BankTransaction | None" = None,
) -> None:
    entry = _sub(voucher, "ALLLEDGERENTRIES.LIST")
    _sub(entry, "LEDGERNAME", ledger_name)
    _sub(entry, "ISDEEMEDPOSITIVE", "Yes" if is_debit else "No")
    # Tally stores debit as negative, credit as positive in the XML amount field
    tally_amount = -round(amount, 2) if is_debit else round(amount, 2)
    _sub(entry, "AMOUNT", str(tally_amount))

    if is_bank_entry and txn is not None:
        alloc = _sub(entry, "BANKALLOCATIONS.LIST")
        _sub(alloc, "DATE", txn.date)
        _sub(alloc, "INSTRUMENTDATE", txn.inst_date or txn.date)
        _sub(alloc, "INSTRUMENTNUMBER", txn.inst_no)
        _sub(alloc, "TRANSACTIONTYPE", txn.transaction_type or "Others")
        _sub(alloc, "PAYMENTFAVOURING", "")
        _sub(alloc, "AMOUNT", str(tally_amount))
