# Tally Prime Importer – by Tuhin

A Python desktop application that reads Excel-based accounting data and converts it into
**Tally Prime-compatible XML** files that you can import directly into Tally Prime.

---

## What It Does

| Feature | Details |
|---|---|
| **Bank Vouchers** | Receipt, Payment, Contra from a bank statement Excel |
| **Sales Vouchers** | Sales invoices with GST (CGST/SGST/IGST) |
| **Purchase Vouchers** | Purchase invoices with input GST |
| **Column Mapping** | Map *your* Excel column names to Tally fields via a UI dialog |
| **Template Save/Load** | Save your column mapping as a named template for re-use |
| **Validation** | In-app error reporting before export |
| **XML Export** | One-click export to `.xml` ready for Tally Prime import |

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.10 or newer | Available at https://www.python.org/downloads/ |
| `tkinter` | Comes bundled with Python on Windows and macOS. On Linux: `sudo apt install python3-tk` |
| pip packages | See `requirements.txt` |

---

## Install

```bash
# 1. Clone the repository
git clone https://github.com/tuhinsbcl2-ctrl/Tally-Prime-Import-by-Tuhin.git
cd Tally-Prime-Import-by-Tuhin

# 2. (Optional but recommended) Create a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## How to Run

```bash
python main.py
```

The application window opens with three tabs:

- **Bank Vouchers**
- **Sales**
- **Purchase**

### Run as a Desktop App (no console window)

On **Windows**, double-click **`run.pyw`** in the repository folder.  
Python must be installed and `.pyw` files must be associated with `pythonw.exe`
(the standard Python installer does this automatically).

### Build a Standalone `.exe` (no Python required on the target PC)

Install PyInstaller and create a single-file executable:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --name "Tally Prime Importer" main.py
```

The resulting `dist/Tally Prime Importer.exe` can be distributed and run on any
Windows PC without Python installed.

---

## Typical Workflow

1. Click **Browse…** and select your Excel file (`.xlsx`).
2. Choose the worksheet from the **Sheet** dropdown.
3. The first 50 rows are shown in the preview table.
4. Click **Map Columns…** to open the mapping dialog.
   - For each Tally field, select the matching column from your Excel file.
   - Save the mapping as a template for future use.
5. Click **Validate & Preview** to check for errors.
   - Validation messages appear at the bottom of the tab.
6. Click **Export XML…** to save the `.xml` file.
7. Import the `.xml` file into Tally Prime (see below).

---

## Importing XML into Tally Prime

1. Open **Tally Prime**.
2. Go to **Gateway of Tally → Import → Data**.
3. Select **Vouchers** as the import type.
4. Browse to the exported `.xml` file.
5. Click **Import**. Tally will process the file and report the number of vouchers imported.

> **Tip:** Make sure the ledger names in your Excel exactly match the ledger names in Tally Prime
> (including capitalisation), or Tally will create new ledgers on import.

---

## Expected Excel Column Layout

### Bank Transactions

| Column (suggested name) | Tally Field | Required |
|---|---|---|
| Date | Date | ✅ |
| Voucher Type | Voucher Type (`Receipt`/`Payment`/`Contra`) | ✅ (or set default in UI) |
| Bank Ledger | Bank / Payment Mode ledger name | ✅ |
| Party Name | Counter-party ledger name | ✅ |
| Amount | Transaction amount (positive number) | ✅ |
| Narration | Narration text | optional |
| Transaction ID | Bank reference / UTR number | optional |
| Voucher No | Internal voucher number | optional |
| Instrument No | Instrument/cheque number (`INSTRUMENTNUMBER` in Tally) | optional |
| Instrument Date | Instrument/cheque date (mapped to `INSTRUMENTDATE` in Tally) | optional |
| Transaction Type | e.g. `e-Fund Transfer`, `Cheque/DD` (defaults to `Others`) | optional |

> **Column names are flexible** – you map them in the app. The names above are suggestions.

### Sales Invoices

| Column | Tally Field | Required |
|---|---|---|
| Party Name | Party name | ✅ |
| Invoice Number | Invoice number | ✅ |
| Entry Date | Voucher date in Tally | ✅ |
| Original Date | Invoice date (reference date) | optional |
| Sales Ledger | Sales account ledger name | ✅ |
| Taxable Amount | Taxable value | ✅ |
| CGST | CGST amount | optional |
| SGST | SGST amount | optional |
| IGST | IGST amount (inter-state) | optional |
| GST Rate | GST % rate | optional |
| Round Off | Rounding difference | optional |
| Total Amount | Invoice total | optional |
| GST Number | Party GSTIN | optional |
| Narration | Narration text | optional |

### Purchase Invoices

Same columns as Sales, but replace **Sales Ledger** with **Purchase Ledger**.

---

## Sample Files

The `samples/` directory contains three ready-to-use Excel files:

| File | Contents |
|---|---|
| `samples/bank_transactions_sample.xlsx` | 4 bank transactions (Receipt, Payment, Contra) |
| `samples/sales_sample.xlsx` | 3 sales invoices with GST |
| `samples/purchase_sample.xlsx` | 2 purchase invoices with GST |

Open these in the app and use **Map Columns…** to see a working example of the full flow.

---

## Project Structure

```
tally_importer/
├── __init__.py
├── models/            # Data models (BankTransaction, SalesEntry, PurchaseEntry)
│   └── __init__.py
├── excel_reader/      # Excel file reading utilities
│   └── __init__.py
├── validator/         # Validation logic for each voucher type
│   └── __init__.py
├── mapping/           # Column mapping definitions and template persistence
│   └── __init__.py
├── xml_generator/     # Tally XML generation
│   ├── __init__.py
│   ├── bank_xml.py
│   ├── sales_xml.py
│   └── purchase_xml.py
└── gui/               # Tkinter user interface
    ├── __init__.py
    ├── app.py          # Root window + notebook
    ├── bank_tab.py
    ├── sales_tab.py
    ├── purchase_tab.py
    └── mapping_dialog.py
main.py                # Entry point
requirements.txt
samples/               # Sample Excel files
tests/                 # Pytest unit tests
```

---

## Tally XML Assumptions (MVP)

Because Tally's exact XML schema depends on your company configuration, the following
assumptions are documented here:

| Assumption | Details |
|---|---|
| Ledger names | Must already exist in Tally. The app uses the exact string from your Excel. |
| GST ledger names | Bank tab uses `CGST`, `SGST`, `IGST` for sales payable; `CGST Input`, `SGST Input`, `IGST Input` for purchase receivable. Rename as needed in Tally. |
| Round Off ledger | Named `Round Off` in generated XML. |
| Voucher numbering | Uses the `Voucher No` column value if present; otherwise a UUID is assigned. |
| Date format | The app auto-detects common formats (`DD-MM-YYYY`, `DD/MM/YYYY`, `YYYY-MM-DD`, etc.) and converts to `YYYYMMDD` for Tally. |
| Company name | XML uses `##SVCurrentCompany` (Tally substitutes the active company at import time). |
| Voucher view | Bank → `Accounting Voucher View`; Sales/Purchase → `Invoice Voucher View`. |

---

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## Current MVP Limitations

- Only `.xlsx` files are supported (`.xls` may work but is untested).
- No master (ledger) creation – all ledgers must already exist in Tally.
- No ODBC/API integration – XML file import only.
- No batch splitting for very large files.
- GST ledger names are hardcoded; future versions will make them configurable.
- No undo/history for mapping changes within a session.

---

## Contributing / Roadmap

Future enhancements planned:

- Configurable GST ledger names
- Auto-creation of missing party masters
- `.xls` and `.csv` support
- Batch export (split by month/voucher type)
- Dark mode UI
