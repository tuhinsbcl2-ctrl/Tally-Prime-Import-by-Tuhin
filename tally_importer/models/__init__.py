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
    inst_no: str = ""           # Instrument Number (cheque no, reference no, etc.)
    inst_date: str = ""         # Instrument Date (YYYYMMDD)
    transaction_type: str = ""  # Transaction type (e.g. "e-Fund Transfer", "Cheque/DD")


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
    voucher_type: str = "Sales"
    hsn_code: str = ""
    cgst_ledger: str = ""
    sgst_ledger: str = ""
    igst_ledger: str = ""
    round_off_ledger: str = ""
    description: str = ""
    place_of_supply: str = ""
    # New fields for sales import with shipping details
    billing_address: str = ""
    shipping_address: str = ""
    billing_state: str = ""
    shipping_state: str = ""
    billing_country: str = ""


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
    voucher_type: str = "Purchase"
    hsn_code: str = ""
    cgst_ledger: str = ""
    sgst_ledger: str = ""
    igst_ledger: str = ""
    round_off_ledger: str = ""
    description: str = ""
    place_of_supply: str = ""


@dataclass
class DebitCreditNoteEntry:
    """Represents a single Debit Note or Credit Note row."""

    party_name: str
    invoice_number: str
    entry_date: str             # YYYYMMDD
    original_date: str          # YYYYMMDD
    note_ledger: str            # Purchase Return / Sales Return ledger
    taxable_amount: float
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    gst_rate: float = 0.0
    round_off: float = 0.0
    total_amount: float = 0.0
    gst_number: str = ""
    narration: str = ""
    voucher_type: str = "Debit Note"   # 'Debit Note' or 'Credit Note'
    hsn_code: str = ""
    cgst_ledger: str = ""
    sgst_ledger: str = ""
    igst_ledger: str = ""
    round_off_ledger: str = ""
    description: str = ""
    place_of_supply: str = ""


@dataclass
class JournalEntry:
    """Represents a single journal entry with debit/credit accounts."""

    date: str                   # YYYYMMDD
    narration: str              # Description of the journal entry
    debit_ledger: str           # Ledger to debit
    debit_amount: float         # Debit amount
    credit_ledger: str          # Ledger to credit
    credit_amount: float        # Credit amount
    reference_number: str = ""  # Optional reference/check number
    invoice_number: str = ""    # Optional invoice reference


# Itemwise sales models (from ITEMWISE_IMPLEMENTATION.md)

@dataclass
class SalesLineItem:
    """Individual line item in an itemwise sales invoice."""
    
    item_name: str
    hsn_code: str
    qty: float
    rate: float
    amount: float              # Auto-calculated: qty * rate
    gst_rate: float
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    unit: str = ""             # UQC (Unit of Quantity and Cost)
    remarks: str = ""


@dataclass
class SalesItemwise:
    """Complete itemwise sales invoice with multiple line items."""
    
    party_name: str
    invoice_number: str
    entry_date: str             # YYYYMMDD
    sales_ledger: str
    line_items: list[SalesLineItem] = field(default_factory=list)
    original_date: str = ""
    gst_number: str = ""
    narration: str = ""
    voucher_type: str = "Sales"
    cgst_ledger: str = ""
    sgst_ledger: str = ""
    igst_ledger: str = ""
    round_off_ledger: str = ""
    place_of_supply: str = ""
    # New shipping and address fields
    billing_address: str = ""
    shipping_address: str = ""
    billing_state: str = ""
    shipping_state: str = ""
    billing_country: str = ""
    
    @property
    def total_taxable(self) -> float:
        """Sum of all line item amounts."""
        return round(sum(item.amount for item in self.line_items), 2)
    
    @property
    def total_cgst(self) -> float:
        """Sum of CGST from all items."""
        return round(sum(item.cgst for item in self.line_items), 2)
    
    @property
    def total_sgst(self) -> float:
        """Sum of SGST from all items."""
        return round(sum(item.sgst for item in self.line_items), 2)
    
    @property
    def total_igst(self) -> float:
        """Sum of IGST from all items."""
        return round(sum(item.igst for item in self.line_items), 2)
    
    @property
    def total_amount(self) -> float:
        """Grand total: taxable + all taxes."""
        return round(self.total_taxable + self.total_cgst + self.total_sgst + self.total_igst, 2)


@dataclass
class PurchaseLineItem:
    """Individual line item in an itemwise purchase invoice."""
    
    item_name: str
    hsn_code: str
    qty: float
    rate: float
    amount: float
    gst_rate: float
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    unit: str = ""
    remarks: str = ""


@dataclass
class PurchaseItemwise:
    """Complete itemwise purchase invoice with multiple line items."""
    
    party_name: str
    invoice_number: str
    entry_date: str
    purchase_ledger: str
    line_items: list[PurchaseLineItem] = field(default_factory=list)
    original_date: str = ""
    gst_number: str = ""
    narration: str = ""
    voucher_type: str = "Purchase"
    cgst_ledger: str = ""
    sgst_ledger: str = ""
    igst_ledger: str = ""
    round_off_ledger: str = ""
    place_of_supply: str = ""
    
    @property
    def total_taxable(self) -> float:
        return round(sum(item.amount for item in self.line_items), 2)
    
    @property
    def total_cgst(self) -> float:
        return round(sum(item.cgst for item in self.line_items), 2)
    
    @property
    def total_sgst(self) -> float:
        return round(sum(item.sgst for item in self.line_items), 2)
    
    @property
    def total_igst(self) -> float:
        return round(sum(item.igst for item in self.line_items), 2)
    
    @property
    def total_amount(self) -> float:
        return round(self.total_taxable + self.total_cgst + self.total_sgst + self.total_igst, 2)


@dataclass
class DebitCreditNoteLineItem:
    """Individual line item in an itemwise debit/credit note."""
    
    item_name: str
    hsn_code: str
    qty: float
    rate: float
    amount: float
    gst_rate: float
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    unit: str = ""
    remarks: str = ""


@dataclass
class DebitCreditNoteItemwise:
    """Complete itemwise debit/credit note with multiple line items."""
    
    party_name: str
    invoice_number: str
    entry_date: str
    note_ledger: str
    line_items: list[DebitCreditNoteLineItem] = field(default_factory=list)
    original_date: str = ""
    gst_number: str = ""
    narration: str = ""
    voucher_type: str = "Debit Note"
    cgst_ledger: str = ""
    sgst_ledger: str = ""
    igst_ledger: str = ""
    round_off_ledger: str = ""
    place_of_supply: str = ""
    
    @property
    def total_taxable(self) -> float:
        return round(sum(item.amount for item in self.line_items), 2)
    
    @property
    def total_cgst(self) -> float:
        return round(sum(item.cgst for item in self.line_items), 2)
    
    @property
    def total_sgst(self) -> float:
        return round(sum(item.sgst for item in self.line_items), 2)
    
    @property
    def total_igst(self) -> float:
        return round(sum(item.igst for item in self.line_items), 2)
    
    @property
    def total_amount(self) -> float:
        return round(self.total_taxable + self.total_cgst + self.total_sgst + self.total_igst, 2)
