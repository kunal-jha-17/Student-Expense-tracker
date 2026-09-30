import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import budget
from budget import BudgetManager, status_for, percent_used
from models import Expense
from validators import ValidationError


class TestBudgetStatus(unittest.TestCase):
    LIMIT = 100000  # Rs 1000.00 in paise

    def test_79_9_percent_is_ok(self):
        self.assertEqual(status_for(79900, self.LIMIT), budget.OK)

    def test_exactly_80_percent_is_warning(self):
        self.assertEqual(status_for(80000, self.LIMIT), budget.WARNING)

    def test_99_9_percent_is_warning(self):
        self.assertEqual(status_for(99900, self.LIMIT), budget.WARNING)

    def test_exactly_100_percent_is_exceeded(self):
        self.assertEqual(status_for(100000, self.LIMIT), budget.EXCEEDED)

    def test_over_100_percent_is_exceeded(self):
        self.assertEqual(status_for(150000, self.LIMIT), budget.EXCEEDED)

    def test_zero_spend_is_ok(self):
        self.assertEqual(status_for(0, self.LIMIT), budget.OK)

    def test_percent_value(self):
        self.assertAlmostEqual(percent_used(80000, self.LIMIT), 80.0)

    def test_zero_limit_rejected(self):
        with self.assertRaises(ValueError):
            status_for(100, 0)


class TestBudgetManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "budgets.json")
        self.bm = BudgetManager(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_set_and_persist_limit(self):
        self.bm.set_limit("food", "2000")
        self.assertEqual(self.bm.limits["Food"], 200000)
        self.assertEqual(BudgetManager(self.path).limits["Food"], 200000)

    def test_unknown_category_rejected(self):
        with self.assertRaises(ValidationError):
            self.bm.set_limit("Gambling", "500")

    def test_negative_or_zero_limit_rejected(self):
        for bad in ("-5", "0"):
            with self.assertRaises(ValidationError):
                self.bm.set_limit("Food", bad)

    def test_report_empty_month(self):
        self.bm.set_limit("Food", "1000")
        lines = self.bm.report([], "2026-09")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].spent, 0)
        self.assertEqual(lines[0].status, budget.OK)

    def test_report_only_counts_selected_month_and_category(self):
        self.bm.set_limit("Food", "1000")
        exps = [
            Expense(1, "2026-09-01", "Food", 85000),
            Expense(2, "2026-08-31", "Food", 99999),     # other month
            Expense(3, "2026-09-02", "Rent", 500000),    # other category
        ]
        line = self.bm.report(exps, "2026-09")[0]
        self.assertEqual(line.spent, 85000)
        self.assertEqual(line.status, budget.WARNING)

    def test_check_category_without_budget_returns_none(self):
        self.assertIsNone(self.bm.check_category([], "Food", "2026-09"))


if __name__ == "__main__":
    unittest.main()
