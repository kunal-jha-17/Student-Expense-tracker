"""Module 3: Analytics (totals, summary, highest category, CSV export)."""
import calendar
from datetime import date
from typing import Optional, Tuple

import storage


def _in_month(expenses, month):
    return [e for e in expenses if e.date[:7] == month]


def category_totals(expenses, month: str) -> dict:
    """Sum of expenses per category for a month (paise), using a dict."""
    totals = {}
    for e in _in_month(expenses, month):
        totals[e.category] = totals.get(e.category, 0) + e.amount
    return totals


def monthly_total(expenses, month: str) -> int:
    return sum(e.amount for e in _in_month(expenses, month))


def highest_category(expenses, month: str) -> Optional[Tuple[str, int]]:
    totals = category_totals(expenses, month)
    if not totals:
        return None
    cat = max(totals, key=totals.get)
    return cat, totals[cat]


def average_daily_spend(expenses, month: str, today: date = None) -> int:
    """Total / days elapsed in the month (paise, rounded).

    Current month: days elapsed = today's day number.
    Past month: all days of that month. Future month: 0.
    """
    today = today or date.today()
    year, mon = int(month[:4]), int(month[5:7])
    if (today.year, today.month) < (year, mon):
        return 0
    days_in_month = calendar.monthrange(year, mon)[1]
    days = today.day if (today.year, today.month) == (year, mon) else days_in_month
    total = monthly_total(expenses, month)
    return (total + days // 2) // days


def top_expenses(expenses, month: str, n: int = 3) -> list:
    return sorted(_in_month(expenses, month), key=lambda e: e.amount, reverse=True)[:n]


def monthly_summary(expenses, month: str, today: date = None) -> dict:
    return {
        "month": month,
        "count": len(_in_month(expenses, month)),
        "total": monthly_total(expenses, month),
        "category_totals": category_totals(expenses, month),
        "highest_category": highest_category(expenses, month),
        "average_daily": average_daily_spend(expenses, month, today),
        "top_expenses": top_expenses(expenses, month, 3),
    }


def export_csv(expenses, path, month: str = None) -> int:
    """CSV export (uses the csv module via storage). Returns rows written."""
    return storage.export_csv(expenses, path, month)
