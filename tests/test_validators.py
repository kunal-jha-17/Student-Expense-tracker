import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validators import (
    ValidationError, format_paise, parse_amount, parse_date, parse_month,
    validate_category,
)

TODAY = date(2026, 9, 30)


class TestValidators(unittest.TestCase):
    def test_valid_date(self):
        self.assertEqual(parse_date("2026-09-15", TODAY), date(2026, 9, 15))

    def test_today_is_allowed(self):
        self.assertEqual(parse_date("2026-09-30", TODAY), TODAY)

    def test_invalid_dates(self):
        for bad in ("2026-13-01", "2026-02-30", "15/09/2026", "abc", "", "  "):
            with self.assertRaises(ValidationError, msg=bad):
                parse_date(bad, TODAY)

    def test_future_date_rejected(self):
        with self.assertRaises(ValidationError):
            parse_date("2026-10-01", TODAY)

    def test_amount_to_paise(self):
        self.assertEqual(parse_amount("125.50"), 12550)
        self.assertEqual(parse_amount("1,000"), 100000)
        self.assertEqual(parse_amount(0.1), 10)   # no float bug

    def test_negative_zero_and_garbage_amounts(self):
        for bad in ("-10", "0", "abc", "", "nan", "inf", "1.234", True):
            with self.assertRaises(ValidationError, msg=str(bad)):
                parse_amount(bad)

    def test_category_case_insensitive(self):
        self.assertEqual(validate_category("  fOoD "), "Food")

    def test_unknown_category(self):
        for bad in ("Gambling", "", None, 5):
            with self.assertRaises(ValidationError):
                validate_category(bad)

    def test_month(self):
        self.assertEqual(parse_month("2026-09"), "2026-09")
        with self.assertRaises(ValidationError):
            parse_month("2026-13")

    def test_format_paise(self):
        self.assertEqual(format_paise(123456), "Rs 1,234.56")
        self.assertEqual(format_paise(5), "Rs 0.05")


if __name__ == "__main__":
    unittest.main()
