"""Module 2: Budget manager (monthly limits + 80% / 100% warnings)."""
from typing import NamedTuple, Optional

import storage
from logger import get_logger
from validators import parse_amount, validate_category

log = get_logger(__name__)

WARN_PERCENT = 80

OK = "OK"
WARNING = "WARNING"
EXCEEDED = "EXCEEDED"


class BudgetLine(NamedTuple):
    category: str
    limit: int      # paise
    spent: int      # paise
    percent: float
    status: str


def percent_used(spent: int, limit: int) -> float:
    if limit <= 0:
        raise ValueError("Budget limit must be positive.")
    return spent / limit * 100


def status_for(spent: int, limit: int) -> str:
    """OK below 80%, WARNING from 80% to under 100%, EXCEEDED at 100% or more.

    Uses integer maths so boundaries are exact (no float rounding surprises).
    """
    if limit <= 0:
        raise ValueError("Budget limit must be positive.")
    if spent >= limit:
        return EXCEEDED
    if spent * 100 >= limit * WARN_PERCENT:
        return WARNING
    return OK


class BudgetManager:
    def __init__(self, path=storage.BUDGETS_PATH):
        self.path = path
        self.limits = storage.load_budgets(path)

    def set_limit(self, category, amount) -> int:
        cat = validate_category(category)
        paise = parse_amount(amount)
        self.limits[cat] = paise
        storage.save_budgets(self.limits, self.path)
        log.info("Set budget %s = %s paise", cat, paise)
        return paise

    def remove_limit(self, category) -> None:
        cat = validate_category(category)
        if cat not in self.limits:
            raise KeyError(f"No budget set for {cat}.")
        del self.limits[cat]
        storage.save_budgets(self.limits, self.path)

    @staticmethod
    def _spent(expenses, category, month) -> int:
        return sum(e.amount for e in expenses
                   if e.category == category and e.date[:7] == month)

    def report(self, expenses, month: str) -> list:
        """Status of every category that has a budget, for the given month."""
        lines = []
        for cat in sorted(self.limits):
            limit = self.limits[cat]
            spent = self._spent(expenses, cat, month)
            lines.append(BudgetLine(cat, limit, spent,
                                    percent_used(spent, limit), status_for(spent, limit)))
        return lines

    def check_category(self, expenses, category, month) -> Optional[BudgetLine]:
        """Budget line for one category, or None if it has no budget."""
        limit = self.limits.get(category)
        if limit is None:
            return None
        spent = self._spent(expenses, category, month)
        return BudgetLine(category, limit, spent,
                          percent_used(spent, limit), status_for(spent, limit))
