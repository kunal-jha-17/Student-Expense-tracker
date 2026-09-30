"""Module 1: Transactions (add, view, edit, delete)."""
from datetime import date

import storage
from logger import get_logger
from models import Expense
from validators import (
    parse_amount, parse_date, validate_category, validate_note,
)

log = get_logger(__name__)


class NotFoundError(LookupError):
    """Raised when an expense id does not exist."""


class TransactionManager:
    def __init__(self, path=storage.EXPENSES_PATH):
        self.path = path
        self.expenses = storage.load_expenses(path)

    def _save(self):
        storage.save_expenses(self.expenses, self.path)

    def _next_id(self) -> int:
        return max((e.id for e in self.expenses), default=0) + 1

    def add(self, date_text, category, amount, note="", today: date = None) -> Expense:
        expense = Expense(
            id=self._next_id(),
            date=parse_date(date_text, today).isoformat(),
            category=validate_category(category),
            amount=parse_amount(amount),
            note=validate_note(note),
        )
        self.expenses.append(expense)
        self._save()
        log.info("Added expense %s", expense)
        return expense

    def get(self, expense_id: int) -> Expense:
        for e in self.expenses:
            if e.id == expense_id:
                return e
        raise NotFoundError(f"No expense with id {expense_id}.")

    def edit(self, expense_id, date_text=None, category=None, amount=None,
             note=None, today: date = None) -> Expense:
        """Update only the fields that are not None. All values validated first."""
        expense = self.get(expense_id)
        new_date = parse_date(date_text, today).isoformat() if date_text is not None else expense.date
        new_cat = validate_category(category) if category is not None else expense.category
        new_amount = parse_amount(amount) if amount is not None else expense.amount
        new_note = validate_note(note) if note is not None else expense.note
        expense.date, expense.category = new_date, new_cat
        expense.amount, expense.note = new_amount, new_note
        self._save()
        log.info("Edited expense %s", expense)
        return expense

    def delete(self, expense_id: int) -> Expense:
        expense = self.get(expense_id)
        self.expenses.remove(expense)
        self._save()
        log.info("Deleted expense %s", expense)
        return expense

    def list(self, month: str = None, category: str = None) -> list:
        result = self.expenses
        if month:
            result = [e for e in result if e.date[:7] == month]
        if category:
            cat = validate_category(category)
            result = [e for e in result if e.category == cat]
        return sorted(result, key=lambda e: (e.date, e.id))
