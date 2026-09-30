# Expense Tracker & Budget Analyzer

A command-line app (pure Python 3.8+, no external packages) that helps students
track their allowance, set category budgets and analyse spending.

## Run

    python main.py

## Test

    python -m unittest discover -s tests -v

(`pytest` also works if installed.)

## Features

| Module | File | What it does |
|---|---|---|
| Transactions | `transactions.py` | Add / view / edit / delete expenses (id, date, category, amount, note) |
| Budget manager | `budget.py` | Monthly limit per category. OK < 80%, WARNING 80% to < 100%, EXCEEDED >= 100%. Alerts appear right after you add or edit an expense |
| Analytics | `analytics.py` | Category totals, monthly total, highest category, average daily spend, top 3 expenses, CSV export |

## Design notes

* **Money is stored as integer paise** (Rs 125.50 -> 12550), so there are no
  float rounding bugs. Budget boundaries use integer maths too
  (`spent * 100 >= limit * 80`).
* **Dates** are validated with `datetime.strptime` in try/except; future dates
  are rejected.
* **Categories**: Food, Rent, Transport, Education, Entertainment, Health,
  Shopping, Utilities, Other (edit `CATEGORIES` in `validators.py`).
* **Average daily spend** = month total / days elapsed (today's day number for
  the current month, full month length for past months).
* **Storage**: `data/expenses.json` and `data/budgets.json`, written atomically.
  A corrupt file gives a clear error instead of a crash.
* **Logging**: actions and errors go to `logs/app.log`.

## Structure

    expense-tracker/
    ├── main.py          # menu / CLI
    ├── models.py        # Expense dataclass
    ├── storage.py       # JSON + CSV I/O
    ├── validators.py    # date, amount, category, month validation
    ├── transactions.py  # Module 1 (CRUD)
    ├── budget.py        # Module 2
    ├── analytics.py     # Module 3
    ├── logger.py
    ├── data/expenses.json, data/budgets.json
    ├── tests/           # test_budget, test_analytics, test_transactions, test_validators
    ├── README.md
    └── statement.md

## Tests cover

Budget boundaries (79.9%, 80%, 100%), empty month, invalid date, future date,
negative/zero amount, unknown category, edit/delete, persistence, corrupt file,
analytics totals, top 3, average daily spend and CSV export.
