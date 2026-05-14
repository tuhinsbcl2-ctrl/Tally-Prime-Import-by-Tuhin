"""Validation logic for bank, sales and purchase data."""
from __future__ import annotations

import logging
from typing import Any

from tally_importer.models import BankTransaction, PurchaseEntry, SalesEntry, SalesItemwise, SalesLineItem


# Valid UQC (Unit of Quantity and Cost) codes
VALID_UQC_CODES = {
    "Pcs": "Pieces",
    "Tonn": "Tonnes",
    "Kgs": "Kilograms",
    "gm": "Grams",
    "Mtr": "Meters",
    "Ltr": "Liters",
    "Box": "Boxes",
    "Pack": "Packs",
    "bags": "Bags",
    "other": "Other",
    "set": "Sets",
    "sq ft": "Square Feet",
    "pair": "Pairs",
    "units": "Units",
}


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Bank transaction validation
# ---------------------------------------------------------------------------

def validate_bank_transactions(
    rows: list[dict[str, Any]],
    mapping: dict[str, str],
    default_voucher_type: str = "",
) -> tuple[list[BankTransaction], list[dict[str, Any]]]:
    """Validate raw bank rows using the provided column *mapping*.

    Returns
    -------
    valid : list of BankTransaction
    errors : list of dicts with keys ``row``, ``errors``
    """
    valid: list[BankTransaction] = []
    errors: list[dict[str, Any]] = []

    def get(row: dict, key: str) -> str:
        col = mapping.get(key, "")
        return str(row.get(col, "")).strip()

    for i, row in enumerate(rows):
        errs: list[str] = []

        date = get(row, "date")
        if not date:
            errs.append("Missing date")

        voucher_type = get(row, "voucher_type") or default_voucher_type
        if voucher_type not in ("Receipt", "Payment", "Contra"):
            errs.append(
                f"Invalid/missing voucher type '{voucher_type}' – must be Receipt, Payment, or Contra"
            )

        bank_ledger = get(row, "bank_ledger")
        if not bank_ledger:
            errs.append("Missing bank/payment-mode ledger")

        party_ledger = get(row, "party_ledger")
        if not party_ledger:
            errs.append("Missing party name/ledger")

        amount_str = get(row, "amount")
        amount = _safe_float(amount_str)
        if amount is None:
            errs.append(f"Invalid amount '{amount_str}'")
        elif amount <= 0:
            errs.append(f"Amount must be positive, got {amount_str}")

        if errs:
            errors.append({"row": i + 2, "errors": errs, "data": row})
        else:
            valid.append(
                BankTransaction(
                    date=_normalize_date(date),
                    voucher_type=voucher_type,
                    bank_ledger=bank_ledger,
                    party_ledger=party_ledger,
                    amount=float(amount),  # type: ignore[arg-type]
                    narration=get(row, "narration"),
                    transaction_id=get(row, "transaction_id"),
                    voucher_number=get(row, "voucher_number"),
                    inst_no=get(row, "inst_no"),
                    inst_date=_normalize_date(get(row, "inst_date")) if get(row, "inst_date") else "",
                    transaction_type=get(row, "transaction_type"),
                )
            )

    return valid, errors


# ---------------------------------------------------------------------------
# Sales validation
# ---------------------------------------------------------------------------

def validate_sales(
    rows: list[dict[str, Any]],
    mapping: dict[str, str],
    default_voucher_type: str = "Sales",
    cgst_ledger: str = "",
    sgst_ledger: str = "",
    igst_ledger: str = "",
    round_off_ledger: str = "",
) -> tuple[list[SalesEntry], list[dict[str, Any]]]:
    valid: list[SalesEntry] = []
    errors: list[dict[str, Any]] = []

    def get(row: dict, key: str) -> str:
        col = mapping.get(key, "")
        return str(row.get(col, "")).strip()

    def fget(row: dict, key: str) -> float:
        val = get(row, key)
        if val in ("-", ""):
            return 0.0
        return _safe_float(val) or 0.0

    for i, row in enumerate(rows):
        errs: list[str] = []

        party_name = get(row, "party_name")
        if not party_name:
            errs.append("Missing party name")

        invoice_number = get(row, "invoice_number")
        if not invoice_number:
            errs.append("Missing invoice number")

        entry_date = get(row, "entry_date")
        if not entry_date:
            errs.append("Missing entry date")

        original_date = get(row, "original_date") or entry_date

        sales_ledger = get(row, "sales_ledger")
        if not sales_ledger:
            errs.append("Missing sales ledger")

        taxable_str = get(row, "taxable_amount")
        taxable = _safe_float(taxable_str)
        if taxable is None:
            errs.append(f"Invalid taxable amount '{taxable_str}'")
            taxable = 0.0

        cgst = fget(row, "cgst")
        sgst = fget(row, "sgst")
        igst = fget(row, "igst")
        round_off = fget(row, "round_off")
        gst_rate = fget(row, "gst_rate")
        total_amount = fget(row, "total_amount")

        # Tax consistency check
        computed_total = round(taxable + cgst + sgst + igst + round_off, 2)
        if total_amount and abs(computed_total - total_amount) > 1.0:
            errs.append(
                f"Tax total mismatch: taxable({taxable}) + taxes({cgst+sgst+igst}) "
                f"+ round_off({round_off}) = {computed_total} ≠ total({total_amount})"
            )

        if errs:
            errors.append({"row": i + 2, "errors": errs, "data": row})
        else:
            voucher_type = get(row, "voucher_type") or default_voucher_type
            valid.append(
                SalesEntry(
                    party_name=party_name,
                    invoice_number=invoice_number,
                    entry_date=_normalize_date(entry_date),
                    original_date=_normalize_date(original_date),
                    sales_ledger=sales_ledger,
                    taxable_amount=float(taxable),
                    cgst=cgst,
                    sgst=sgst,
                    igst=igst,
                    gst_rate=gst_rate,
                    round_off=round_off,
                    total_amount=total_amount or computed_total,
                    gst_number=get(row, "gst_number"),
                    narration=get(row, "narration"),
                    voucher_type=voucher_type,
                    hsn_code=get(row, "hsn_code"),
                    cgst_ledger=cgst_ledger,
                    sgst_ledger=sgst_ledger,
                    igst_ledger=igst_ledger,
                    round_off_ledger=round_off_ledger,
                    description=get(row, "description"),
                    place_of_supply=get(row, "place_of_supply"),
                )
            )

    return valid, errors


# ---------------------------------------------------------------------------
# Sales Itemwise validation
# ---------------------------------------------------------------------------

def validate_sales_itemwise(
    rows: list[dict[str, Any]],
    mapping: dict[str, str],
    default_voucher_type: str = "Sales",
    cgst_ledger: str = "",
    sgst_ledger: str = "",
    igst_ledger: str = "",
    round_off_ledger: str = "",
) -> tuple[list[SalesItemwise], list[dict[str, Any]]]:
    """Validate itemwise sales rows and group by invoice number.
    
    Supports multiple items per invoice where header details (Date, Invoice No, 
    Customer, etc.) repeat for each line item.
    
    Returns
    -------
    valid : list of SalesItemwise (grouped by invoice)
    errors : list of dicts with keys ``row``, ``errors``
    """
    valid: list[SalesItemwise] = []
    errors: list[dict[str, Any]] = []
    invoice_map: dict[str, SalesItemwise] = {}  # Key: (date, invoice_number, party_name)

    def get(row: dict, key: str) -> str:
        col = mapping.get(key, "")
        return str(row.get(col, "")).strip()

    def fget(row: dict, key: str) -> float:
        val = get(row, key)
        if val in ("-", ""):
            return 0.0
        return _safe_float(val) or 0.0

    for i, row in enumerate(rows):
        errs: list[str] = []

        # Header fields (must be present in every row)
        party_name = get(row, "party_name")
        if not party_name:
            errs.append("Missing party name")

        invoice_number = get(row, "invoice_number")
        if not invoice_number:
            errs.append("Missing invoice number")

        entry_date = get(row, "entry_date")
        if not entry_date:
            errs.append("Missing entry date")

        sales_ledger = get(row, "sales_ledger")
        if not sales_ledger:
            errs.append("Missing sales ledger")

        # Line item fields
        item_name = get(row, "item_name")
        if not item_name:
            errs.append("Missing item name/description")

        hsn_code = get(row, "hsn_code")
        if not hsn_code:
            errs.append("Missing HSN/SAC code")

        qty_str = get(row, "qty")
        qty = _safe_float(qty_str)
        if qty is None or qty <= 0:
            errs.append(f"Invalid quantity '{qty_str}' – must be positive")
            qty = 0.0

        rate_str = get(row, "rate")
        rate = _safe_float(rate_str)
        if rate is None or rate <= 0:
            errs.append(f"Invalid rate '{rate_str}' – must be positive")
            rate = 0.0

        uqc = get(row, "uqc")
        if not uqc:
            errs.append("Missing UQC (Unit of Quantity and Cost)")
        elif uqc not in VALID_UQC_CODES:
            errs.append(
                f"Invalid UQC '{uqc}'. Valid options: {', '.join(VALID_UQC_CODES.keys())}"
            )

        gst_rate = fget(row, "gst_rate")
        if not gst_rate:
            errs.append("Missing GST rate for item")

        cgst = fget(row, "cgst")
        sgst = fget(row, "sgst")
        igst = fget(row, "igst")
        remarks = get(row, "remarks")

        # Calculate line amount
        line_amount = round(qty * rate, 2) if qty > 0 and rate > 0 else 0.0

        # Validate GST amount consistency
        computed_gst = round(cgst + sgst + igst, 2)
        expected_gst = round(line_amount * (gst_rate / 100), 2) if gst_rate > 0 else 0.0
        
        if expected_gst > 0 and abs(computed_gst - expected_gst) > 1.0:
            errs.append(
                f"GST amount mismatch for item: computed GST ({cgst}+{sgst}+{igst}={computed_gst}) "
                f"≠ expected ({expected_gst} at {gst_rate}%)"
            )

        if errs:
            errors.append({"row": i + 2, "errors": errs, "data": row})
        else:
            # Group by invoice key
            invoice_key = (entry_date, invoice_number, party_name)
            
            # Create line item
            line_item = SalesLineItem(
                item_name=item_name,
                hsn_code=hsn_code,
                qty=float(qty),
                rate=float(rate),
                amount=line_amount,
                gst_rate=gst_rate,
                cgst=cgst,
                sgst=sgst,
                igst=igst,
                remarks=remarks,
                unit=uqc,
            )

            if invoice_key not in invoice_map:
                # Create new invoice entry
                original_date = get(row, "original_date") or entry_date
                voucher_type = get(row, "voucher_type") or default_voucher_type
                
                invoice_map[invoice_key] = SalesItemwise(
                    party_name=party_name,
                    invoice_number=invoice_number,
                    entry_date=_normalize_date(entry_date),
                    original_date=_normalize_date(original_date),
                    sales_ledger=sales_ledger,
                    gst_number=get(row, "gst_number"),
                    narration=get(row, "narration"),
                    voucher_type=voucher_type,
                    cgst_ledger=cgst_ledger,
                    sgst_ledger=sgst_ledger,
                    igst_ledger=igst_ledger,
                    round_off_ledger=round_off_ledger,
                    place_of_supply=get(row, "place_of_supply"),
                    line_items=[line_item],
                )
            else:
                # Add item to existing invoice
                invoice_map[invoice_key].line_items.append(line_item)

    # Convert map to list
    valid = list(invoice_map.values())
    
    return valid, errors


# ---------------------------------------------------------------------------
# Purchase validation
# ---------------------------------------------------------------------------

def validate_purchase(
    rows: list[dict[str, Any]],
    mapping: dict[str, str],
    default_voucher_type: str = "Purchase",
    cgst_ledger: str = "",
    sgst_ledger: str = "",
    igst_ledger: str = "",
    round_off_ledger: str = "",
) -> tuple[list[PurchaseEntry], list[dict[str, Any]]]:
    valid: list[PurchaseEntry] = []
    errors: list[dict[str, Any]] = []

    def get(row: dict, key: str) -> str:
        col = mapping.get(key, "")
        return str(row.get(col, "")).strip()

    def fget(row: dict, key: str) -> float:
        val = get(row, key)
        if val in ("-", ""):
            return 0.0
        return _safe_float(val) or 0.0

    for i, row in enumerate(rows):
        errs: list[str] = []

        party_name = get(row, "party_name")
        if not party_name:
            errs.append("Missing party name")

        invoice_number = get(row, "invoice_number")
        if not invoice_number:
            errs.append("Missing invoice number")

        entry_date = get(row, "entry_date")
        if not entry_date:
            errs.append("Missing entry date")

        original_date = get(row, "original_date") or entry_date

        purchase_ledger = get(row, "purchase_ledger")
        if not purchase_ledger:
            errs.append("Missing purchase ledger")

        taxable_str = get(row, "taxable_amount")
        taxable = _safe_float(taxable_str)
        if taxable is None:
            errs.append(f"Invalid taxable amount '{taxable_str}'")
            taxable = 0.0

        cgst = fget(row, "cgst")
        sgst = fget(row, "sgst")
        igst = fget(row, "igst")
        round_off = fget(row, "round_off")
        gst_rate = fget(row, "gst_rate")
        total_amount = fget(row, "total_amount")

        computed_total = round(taxable + cgst + sgst + igst + round_off, 2)
        if total_amount and abs(computed_total - total_amount) > 1.0:
            errs.append(
                f"Tax total mismatch: taxable({taxable}) + taxes({cgst+sgst+igst}) "
                f"+ round_off({round_off}) = {computed_total} ≠ total({total_amount})"
            )

        if errs:
            errors.append({"row": i + 2, "errors": errs, "data": row})
        else:
            voucher_type = get(row, "voucher_type") or default_voucher_type
            valid.append(
                PurchaseEntry(
                    party_name=party_name,
                    invoice_number=invoice_number,
                    entry_date=_normalize_date(entry_date),
                    original_date=_normalize_date(original_date),
                    purchase_ledger=purchase_ledger,
                    taxable_amount=float(taxable),
                    cgst=cgst,
                    sgst=sgst,
                    igst=igst,
                    gst_rate=gst_rate,
                    round_off=round_off,
                    total_amount=total_amount or computed_total,
                    gst_number=get(row, "gst_number"),
                    narration=get(row, "narration"),
                    voucher_type=voucher_type,
                    hsn_code=get(row, "hsn_code"),
                    cgst_ledger=cgst_ledger,
                    sgst_ledger=sgst_ledger,
                    igst_ledger=igst_ledger,
                    round_off_ledger=round_off_ledger,
                    description=get(row, "description"),
                    place_of_supply=get(row, "place_of_supply"),
                )
            )

    return valid, errors


# ---------------------------------------------------------------------------
# Debit / Credit Note validation
# ---------------------------------------------------------------------------

def validate_debit_credit_note(
    rows: list[dict[str, Any]],
    mapping: dict[str, str],
    default_voucher_type: str = "Debit Note",
    cgst_ledger: str = "",
    sgst_ledger: str = "",
    igst_ledger: str = "",
    round_off_ledger: str = "",
) -> tuple[list[Any], list[dict[str, Any]]]:
    from tally_importer.models import DebitCreditNoteEntry

    valid: list[DebitCreditNoteEntry] = []
    errors: list[dict[str, Any]] = []

    def get(row: dict, key: str) -> str:
        col = mapping.get(key, "")
        return str(row.get(col, "")).strip()

    def fget(row: dict, key: str) -> float:
        val = get(row, key)
        if val in ("-", ""):
            return 0.0
        return _safe_float(val) or 0.0

    for i, row in enumerate(rows):
        errs: list[str] = []

        party_name = get(row, "party_name")
        if not party_name:
            errs.append("Missing party name")

        invoice_number = get(row, "invoice_number")
        if not invoice_number:
            errs.append("Missing invoice/note number")

        entry_date = get(row, "entry_date")
        if not entry_date:
            errs.append("Missing entry date")

        original_date = get(row, "original_date") or entry_date

        note_ledger = get(row, "note_ledger")
        if not note_ledger:
            errs.append("Missing note ledger")

        taxable_str = get(row, "taxable_amount")
        taxable = _safe_float(taxable_str)
        if taxable is None:
            errs.append(f"Invalid taxable amount '{taxable_str}'")
            taxable = 0.0

        cgst = fget(row, "cgst")
        sgst = fget(row, "sgst")
        igst = fget(row, "igst")
        round_off = fget(row, "round_off")
        gst_rate = fget(row, "gst_rate")
        total_amount = fget(row, "total_amount")

        computed_total = round(taxable + cgst + sgst + igst + round_off, 2)
        if total_amount and abs(computed_total - total_amount) > 1.0:
            errs.append(
                f"Tax total mismatch: taxable({taxable}) + taxes({cgst+sgst+igst}) "
                f"+ round_off({round_off}) = {computed_total} ≠ total({total_amount})"
            )

        if errs:
            errors.append({"row": i + 2, "errors": errs, "data": row})
        else:
            voucher_type = get(row, "voucher_type") or default_voucher_type
            valid.append(
                DebitCreditNoteEntry(
                    party_name=party_name,
                    invoice_number=invoice_number,
                    entry_date=_normalize_date(entry_date),
                    original_date=_normalize_date(original_date),
                    note_ledger=note_ledger,
                    taxable_amount=float(taxable),
                    cgst=cgst,
                    sgst=sgst,
                    igst=igst,
                    gst_rate=gst_rate,
                    round_off=round_off,
                    total_amount=total_amount or computed_total,
                    gst_number=get(row, "gst_number"),
                    narration=get(row, "narration"),
                    voucher_type=voucher_type,
                    hsn_code=get(row, "hsn_code"),
                    cgst_ledger=cgst_ledger,
                    sgst_ledger=sgst_ledger,
                    igst_ledger=igst_ledger,
                    round_off_ledger=round_off_ledger,
                    description=get(row, "description"),
                    place_of_supply=get(row, "place_of_supply"),
                )
            )

    return valid, errors


# ---------------------------------------------------------------------------
# Date normalisation helper
# ---------------------------------------------------------------------------

def _normalize_date(date_str: str) -> str:
    """Try to convert various date formats to YYYYMMDD for Tally."""
    import re
    from datetime import datetime

    date_str = date_str.strip()

    # Already in YYYYMMDD
    if re.fullmatch(r"\d{8}", date_str):
        return date_str

    # Strip trailing ".0" (e.g. from numeric Excel serial read as string)
    date_str = re.sub(r"\.0$", "", date_str).strip()

    # Strip trailing time portion " HH:MM:SS" so the remaining formats match
    date_str = re.sub(r"\s+\d{1,2}:\d{2}(:\d{2})?$", "", date_str).strip()

    for fmt in (
        "%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d",
        "%d-%b-%Y", "%d %b %Y", "%b %d, %Y",
        "%d-%m-%y", "%d/%m/%y",
    ):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y%m%d")
        except ValueError:
            continue

    # Return as-is; validation will flag it if needed
    logging.warning("_normalize_date: unrecognized date format %r – passing through as-is", date_str)
    return date_str
