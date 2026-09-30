# Expense Tracker & Budget Analyzer

A command-line application for tracking personal expenses, setting monthly category budgets, and analysing spending. Built for students who want to see where their monthly allowance goes and get warned *before* they overspend.

Pure Python 3.8+ with **no external dependencies**.

---

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Budget Rules](#budget-rules)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Data Storage](#data-storage)
- [Testing](#testing)
- [Customisation](#customisation)

---

## Features

| Module | File | Description |
|---|---|---|
| **Transactions** | `transactions.py` | Add, view, edit and delete expenses (id, date, category, amount, note) |
| **Budget Manager** | `budget.py` | Set a monthly limit per category and get alerts at 80% and 100% usage |
| **Analytics** | `analytics.py` | Category totals, monthly total, highest-spending category, average daily spend, top 3 expenses |
| **Export** | `storage.py` | Export all expenses, or a single month, to CSV |

Other highlights:

- Strict input validation (dates, amounts, categories, months, notes)
- Instant budget alerts right after you add or edit an expense
- Atomic file writes and clear error messages for corrupt data files
- Action and error logging to `logs/app.log`

---

## Getting Started

### Requirements

- Python 3.8 or newer

### Run

```bash
python main.py
```

No installation step is needed.

---

## Usage

Launching the app shows an interactive menu:

```
========== EXPENSE TRACKER ==========
 1. Add expense
 2. View expenses
 3. Edit expense
 4. Delete expense
 5. Set monthly budget for a category
 6. Budget status
 7. Analytics summary
 8. Export to CSV
 0. Exit
```

| Option | What happens |
|---|---|
| **1. Add expense** | Prompts for date (defaults to today), category, amount in rupees and an optional note. A budget alert is shown if the category is at or above 80% of its limit. |
| **2. View expenses** | Lists expenses sorted by date, with a running total. Filter by month (`YYYY-MM`) or press Enter for all. |
| **3. Edit expense** | Pick an expense by ID. Press Enter on any field to keep its current value. |
| **4. Delete expense** | Pick an expense by ID and confirm with `y`. |
| **5. Set monthly budget** | Set (or overwrite) the monthly limit for a category. |
| **6. Budget status** | Shows spent / limit / percent used / status for every category with a budget. |
| **7. Analytics summary** | Monthly total, transaction count, average daily spend, highest category, category totals and top 3 expenses. |
| **8. Export to CSV** | Writes expenses to a CSV file (default name `expenses_<month or all>.csv`). |

### Input formats

| Field | Format | Rules |
|---|---|---|
| Date | `YYYY-MM-DD` | Must be a real date; future dates are rejected |
| Month | `YYYY-MM` | Must be a valid month |
| Amount | e.g. `125.50` | Greater than 0, at most 2 decimal places; commas allowed (`1,250`) |
| Category | See [Customisation](#customisation) | Case-insensitive |
| Note | Free text | Optional, max 200 characters |

### Example session

```
Choose an option: 1
Categories: Food, Rent, Transport, Education, Entertainment, Health, Shopping, Utilities, Other
Date (YYYY-MM-DD) [2026-09-30]:
Category: food
Amount in rupees: 450.50
Note (optional):  Lunch with friends
Added expense #1: Rs 450.50 on Food.
  ! Warning: Food budget at 90.1% (Rs 450.50 of Rs 500.00)
```

---

## Budget Rules

Status is determined by how much of a category's monthly limit has been spent:

| Status | Condition |
|---|---|
| `OK` | Below 80% |
| `WARNING` | 80% up to (but not including) 100% |
| `EXCEEDED` | 100% or more |

Budgets are tracked **per category, per calendar month**. Categories without a budget are never flagged.

---

## Project Structure

```
expense-tracker/
├── main.py            # Interactive menu / CLI entry point
├── models.py          # Expense dataclass
├── storage.py         # JSON persistence + CSV export
├── validators.py      # Date, amount, category, month, note validation + formatting
├── transactions.py    # Module 1: expense CRUD
├── budget.py          # Module 2: budgets and alerts
├── analytics.py       # Module 3: summaries and reports
├── logger.py          # Logging setup (logs/app.log)
├── data/
│   ├── expenses.json  # Saved expenses
│   └── budgets.json   # Saved budgets
├── tests/
│   ├── test_analytics.py
│   ├── test_budget.py
│   ├── test_transactions.py
│   └── test_validators.py
├── README.md
└── statement.md       # Problem statement and solution overview
```

---

## Design Decisions

- **Money is stored as integer paise** (Rs 125.50 → `12550`). This avoids floating-point rounding bugs. Budget thresholds also use integer maths (`spent * 100 >= limit * 80`), so the 80% and 100% boundaries are exact.
- **Amount parsing uses `Decimal`**, so input like `0.1 + 0.2`-style surprises can't creep in and values with more than 2 decimal places are rejected.
- **Average daily spend** = monthly total ÷ days elapsed. For the current month that is today's day number; for past months it is the full month length; for future months it is 0.
- **IDs are never reused.** New expenses get `max(existing id) + 1`.
- **Edits are all-or-nothing.** Every new value is validated before any field is changed, so a bad input leaves the record untouched.
- **Logging never crashes the app.** If the log folder isn't writable, logging silently falls back to a no-op handler.

---

## Data Storage

Data is stored as plain JSON in the `data/` folder and is easy to inspect or back up.

**`data/expenses.json`**, a list of expenses (amounts in paise):

```json
[
  {
    "id": 1,
    "date": "2026-09-30",
    "category": "Food",
    "amount": 45050,
    "note": "Lunch with friends"
  }
]
```

**`data/budgets.json`**, category → monthly limit in paise:

```json
{
  "Food": 500000,
  "Transport": 200000
}
```

Writes are **atomic** (written to a temp file, then swapped in), so a crash mid-save cannot leave a half-written file. If a data file is corrupt or has the wrong shape, the app reports a clear error instead of crashing with a traceback.

### CSV export format

```
id,date,category,amount_rupees,note
1,2026-09-30,Food,450.50,Lunch with friends
```

Rows are sorted by date, then ID.

---

## Testing

Run the full test suite with the standard library:

```bash
python -m unittest discover -s tests -v
```

`pytest` also works if you have it installed:

```bash
pytest
```

The tests cover:

- **Budget boundaries:** 79.9% (OK), exactly 80% (WARNING), 99.9% (WARNING), exactly 100% and above (EXCEEDED), zero spend, invalid limits
- **Validation:** invalid and future dates, negative/zero/garbage amounts, unknown categories, month parsing, currency formatting
- **Transactions:** add and persist, ID incrementing, partial edits, failed edits leaving data untouched, delete, missing IDs, filtering and sorting, corrupt data files
- **Analytics:** category totals, monthly total, highest category, top 3 (including fewer than 3), average daily spend (current, past and future months), empty months, CSV export

---

## Customisation

**Add or rename categories** by editing the `CATEGORIES` list in `validators.py`:

```python
CATEGORIES = [
    "Food", "Rent", "Transport", "Education",
    "Entertainment", "Health", "Shopping", "Utilities", "Other",
]
```

**Change the warning threshold** by editing `WARN_PERCENT` in `budget.py` (default `80`).

**Change the maximum note length** by editing `MAX_NOTE_LENGTH` in `validators.py` (default `200`).
