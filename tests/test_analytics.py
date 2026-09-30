import csv
import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import analytics
from models import Expense

EXPENSES = [
    Expense(1, "2026-09-01", "Food", 25000, "groceries"),
    Expense(2, "2026-09-03", "Rent", 500000, "room"),
    Expense(3, "2026-09-05", "Food", 15000, "dinner"),
    Expense(4, "2026-09-07", "Transport", 5000, "metro"),
    Expense(5, "2026-09-09", "Entertainment", 30000, "movie"),
    Expense(6, "2026-08-20", "Food", 99900, "other month"),
]


class TestAnalytics(unittest.TestCase):
    def test_category_totals(self):
        self.assertEqual(
            analytics.category_totals(EXPENSES, "2026-09"),
            {"Food": 40000, "Rent": 500000, "Transport": 5000, "Entertainment": 30000},
        )

    def test_monthly_total(self):
        self.assertEqual(analytics.monthly_total(EXPENSES, "2026-09"), 575000)

    def test_highest_category(self):
        self.assertEqual(analytics.highest_category(EXPENSES, "2026-09"), ("Rent", 500000))

    def test_top_three_expenses(self):
        top = analytics.top_expenses(EXPENSES, "2026-09", 3)
        self.assertEqual([e.id for e in top], [2, 5, 1])

    def test_average_daily_current_month(self):
        # total 575000 paise over 10 days elapsed = 57500
        self.assertEqual(
            analytics.average_daily_spend(EXPENSES, "2026-09", today=date(2026, 9, 10)), 57500)

    def test_average_daily_past_month_uses_full_month(self):
        # Aug: 99900 / 31 days = 3222.58 -> 3223
        self.assertEqual(
            analytics.average_daily_spend(EXPENSES, "2026-08", today=date(2026, 9, 10)), 3223)

    def test_average_daily_future_month_is_zero(self):
        self.assertEqual(
            analytics.average_daily_spend(EXPENSES, "2026-12", today=date(2026, 9, 10)), 0)

    def test_empty_month(self):
        self.assertEqual(analytics.category_totals([], "2026-09"), {})
        self.assertEqual(analytics.monthly_total([], "2026-09"), 0)
        self.assertIsNone(analytics.highest_category([], "2026-09"))
        self.assertEqual(analytics.top_expenses([], "2026-09"), [])
        self.assertEqual(analytics.average_daily_spend([], "2026-09", today=date(2026, 9, 10)), 0)

    def test_fewer_than_three_expenses(self):
        self.assertEqual(len(analytics.top_expenses(EXPENSES[:2], "2026-09", 3)), 2)

    def test_summary_keys(self):
        s = analytics.monthly_summary(EXPENSES, "2026-09", today=date(2026, 9, 10))
        self.assertEqual(s["count"], 5)
        self.assertEqual(s["total"], 575000)
        self.assertEqual(s["highest_category"][0], "Rent")

    def test_csv_export_month(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.csv")
            count = analytics.export_csv(EXPENSES, path, "2026-09")
            self.assertEqual(count, 5)
            with open(path, newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[0], ["id", "date", "category", "amount_rupees", "note"])
            self.assertEqual(len(rows), 6)
            self.assertEqual(rows[1], ["1", "2026-09-01", "Food", "250.00", "groceries"])

    def test_csv_export_empty_month_has_header_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.csv")
            self.assertEqual(analytics.export_csv(EXPENSES, path, "2020-01"), 0)
            with open(path, newline="", encoding="utf-8") as f:
                self.assertEqual(len(list(csv.reader(f))), 1)


if __name__ == "__main__":
    unittest.main()
