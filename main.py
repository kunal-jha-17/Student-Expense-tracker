"""Expense Tracker & Budget Analyzer - command line interface.

Run:  python main.py
"""
from datetime import date

import analytics
import budget
import storage
from budget import BudgetManager
from logger import get_logger
from transactions import NotFoundError, TransactionManager
from validators import (
    CATEGORIES, ValidationError, format_paise, parse_amount, parse_date,
    parse_month, validate_category, validate_note,
)

log = get_logger("main")

MENU = """
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
"""


def ask(label, parser=lambda x: x, default=None):
    """Prompt until `parser` accepts the input (or default is used on Enter)."""
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{label}{suffix}: ").strip()
        if not raw and default is not None:
            raw = str(default)
        try:
            return parser(raw)
        except ValidationError as exc:
            print(f"  ! {exc}")


def ask_optional(label, parser):
    """Enter = keep existing value (returns None)."""
    while True:
        raw = input(f"{label} (Enter to keep): ").strip()
        if not raw:
            return None
        try:
            parser(raw)           # validate now so the user can retry
            return raw
        except ValidationError as exc:
            print(f"  ! {exc}")


def rupees(paise):
    """Paise -> exact rupee string (avoids float conversion)."""
    return f"{paise // 100}.{paise % 100:02d}"


def current_month():
    return date.today().strftime("%Y-%m")


def ask_month():
    return ask("Month (YYYY-MM)", parse_month, default=current_month())


def print_expenses(expenses):
    if not expenses:
        print("No expenses found.")
        return
    print(f"{'ID':<5}{'Date':<12}{'Category':<15}{'Amount':>14}  Note")
    print("-" * 60)
    for e in expenses:
        print(f"{e.id:<5}{e.date:<12}{e.category:<15}{format_paise(e.amount):>14}  {e.note}")
    print("-" * 60)
    print(f"Total: {format_paise(sum(e.amount for e in expenses))}")


def show_budget_alert(bm, tm, expense):
    line = bm.check_category(tm.expenses, expense.category, expense.date[:7])
    if line is None or line.status == budget.OK:
        return
    if line.status == budget.EXCEEDED:
        print(f"  !! BUDGET EXCEEDED for {line.category}: {format_paise(line.spent)} "
              f"of {format_paise(line.limit)} ({line.percent:.1f}%)")
    else:
        print(f"  ! Warning: {line.category} budget at {line.percent:.1f}% "
              f"({format_paise(line.spent)} of {format_paise(line.limit)})")


def add_expense(tm, bm):
    print(f"Categories: {', '.join(CATEGORIES)}")
    d = ask("Date (YYYY-MM-DD)", parse_date, default=date.today().isoformat())
    category = ask("Category", validate_category)
    amount = ask("Amount in rupees", parse_amount)
    note = ask("Note (optional)", validate_note, default="")
    expense = tm.add(d.isoformat(), category, rupees(amount), note)
    print(f"Added expense #{expense.id}: {format_paise(expense.amount)} on {expense.category}.")
    show_budget_alert(bm, tm, expense)


def view_expenses(tm):
    raw = input("Month (YYYY-MM) or Enter for all: ").strip()
    month = None
    if raw:
        try:
            month = parse_month(raw)
        except ValidationError as exc:
            print(f"  ! {exc}")
            return
    print_expenses(tm.list(month=month))


def edit_expense(tm, bm):
    print_expenses(tm.list())
    try:
        expense_id = int(input("ID of expense to edit: ").strip())
        tm.get(expense_id)
    except ValueError:
        print("  ! ID must be a number.")
        return
    except NotFoundError as exc:
        print(f"  ! {exc}")
        return
    d = ask_optional("New date (YYYY-MM-DD)", parse_date)
    c = ask_optional("New category", validate_category)
    a = ask_optional("New amount in rupees", parse_amount)
    n = ask_optional("New note", validate_note)
    expense = tm.edit(expense_id, d, c, a, n)
    print(f"Updated expense #{expense.id}.")
    show_budget_alert(bm, tm, expense)


def delete_expense(tm):
    print_expenses(tm.list())
    try:
        expense_id = int(input("ID of expense to delete: ").strip())
        expense = tm.get(expense_id)
    except ValueError:
        print("  ! ID must be a number.")
        return
    except NotFoundError as exc:
        print(f"  ! {exc}")
        return
    if input(f"Delete '{expense.category} {format_paise(expense.amount)}'? (y/N): ").strip().lower() == "y":
        tm.delete(expense_id)
        print("Deleted.")
    else:
        print("Cancelled.")


def set_budget(bm):
    print(f"Categories: {', '.join(CATEGORIES)}")
    category = ask("Category", validate_category)
    amount = ask("Monthly limit in rupees", parse_amount)
    bm.set_limit(category, rupees(amount))
    print(f"Budget for {category} set to {format_paise(amount)} per month.")


def budget_status(tm, bm):
    month = ask_month()
    lines = bm.report(tm.expenses, month)
    if not lines:
        print("No budgets set yet. Use option 5.")
        return
    print(f"\nBudget status for {month}")
    print(f"{'Category':<15}{'Spent':>14}{'Limit':>14}{'Used':>9}  Status")
    print("-" * 62)
    for ln in lines:
        print(f"{ln.category:<15}{format_paise(ln.spent):>14}{format_paise(ln.limit):>14}"
              f"{ln.percent:>8.1f}%  {ln.status}")


def show_analytics(tm):
    month = ask_month()
    s = analytics.monthly_summary(tm.expenses, month)
    print(f"\n===== Summary for {month} =====")
    if s["count"] == 0:
        print("No expenses recorded for this month.")
        return
    print(f"Transactions      : {s['count']}")
    print(f"Monthly total     : {format_paise(s['total'])}")
    print(f"Avg daily spend   : {format_paise(s['average_daily'])}")
    cat, amt = s["highest_category"]
    print(f"Highest category  : {cat} ({format_paise(amt)})")
    print("\nCategory totals:")
    for c, t in sorted(s["category_totals"].items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {c:<15}{format_paise(t):>14}")
    print("\nTop 3 largest expenses:")
    for e in s["top_expenses"]:
        print(f"  {e.date}  {e.category:<14}{format_paise(e.amount):>14}  {e.note}")


def export_data(tm):
    raw = input("Month (YYYY-MM) or Enter for all: ").strip()
    month = None
    if raw:
        try:
            month = parse_month(raw)
        except ValidationError as exc:
            print(f"  ! {exc}")
            return
    default = f"expenses_{month or 'all'}.csv"
    path = input(f"File name [{default}]: ").strip() or default
    count = analytics.export_csv(tm.expenses, path, month)
    print(f"Exported {count} expense(s) to {path}.")


def main():
    try:
        tm = TransactionManager()
        bm = BudgetManager()
    except storage.StorageError as exc:
        print(f"Startup error: {exc}")
        log.error("Startup error: %s", exc)
        return 1

    actions = {
        "1": lambda: add_expense(tm, bm),
        "2": lambda: view_expenses(tm),
        "3": lambda: edit_expense(tm, bm),
        "4": lambda: delete_expense(tm),
        "5": lambda: set_budget(bm),
        "6": lambda: budget_status(tm, bm),
        "7": lambda: show_analytics(tm),
        "8": lambda: export_data(tm),
    }
    while True:
        print(MENU)
        try:
            choice = input("Choose an option: ").strip()
            if choice == "0":
                print("Goodbye!")
                return 0
            action = actions.get(choice)
            if action is None:
                print("  ! Invalid choice, try again.")
                continue
            action()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            return 0
        except (storage.StorageError, NotFoundError, ValidationError) as exc:
            print(f"  ! {exc}")
            log.error("%s", exc)


if __name__ == "__main__":
    raise SystemExit(main())
