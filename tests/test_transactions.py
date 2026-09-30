import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import storage
from transactions import NotFoundError, TransactionManager
from validators import ValidationError

TODAY = date(2026, 9, 30)


class TestTransactions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "expenses.json")
        self.tm = TransactionManager(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, **kw):
        args = dict(date_text="2026-09-10", category="Food", amount="100", note="x", today=TODAY)
        args.update(kw)
        return self.tm.add(**args)

    def test_add_and_persist(self):
        e = self.add(amount="99.99")
        self.assertEqual((e.id, e.amount, e.category), (1, 9999, "Food"))
        reloaded = TransactionManager(self.path)
        self.assertEqual(len(reloaded.expenses), 1)
        self.assertEqual(reloaded.expenses[0].amount, 9999)

    def test_ids_increment_and_are_not_reused(self):
        a, b = self.add(), self.add()
        self.tm.delete(a.id)
        c = self.add()
        self.assertEqual((a.id, b.id, c.id), (1, 2, 3))

    def test_invalid_date_rejected_and_nothing_saved(self):
        with self.assertRaises(ValidationError):
            self.add(date_text="2026-99-99")
        self.assertEqual(self.tm.expenses, [])

    def test_future_date_rejected(self):
        with self.assertRaises(ValidationError):
            self.add(date_text="2026-12-01")

    def test_negative_amount_rejected(self):
        with self.assertRaises(ValidationError):
            self.add(amount="-50")

    def test_unknown_category_rejected(self):
        with self.assertRaises(ValidationError):
            self.add(category="Crypto")

    def test_edit_changes_only_given_fields(self):
        e = self.add(amount="100", note="old")
        self.tm.edit(e.id, amount="250", today=TODAY)
        got = self.tm.get(e.id)
        self.assertEqual((got.amount, got.note, got.category), (25000, "old", "Food"))

    def test_edit_invalid_value_leaves_record_untouched(self):
        e = self.add()
        with self.assertRaises(ValidationError):
            self.tm.edit(e.id, category="Food", amount="-1")
        self.assertEqual(self.tm.get(e.id).amount, 10000)

    def test_delete_and_missing_id(self):
        e = self.add()
        self.tm.delete(e.id)
        with self.assertRaises(NotFoundError):
            self.tm.get(e.id)
        with self.assertRaises(NotFoundError):
            self.tm.delete(999)

    def test_list_filters_and_sorted(self):
        self.add(date_text="2026-09-12")
        self.add(date_text="2026-09-01", category="Rent")
        self.add(date_text="2026-08-15")
        self.assertEqual(len(self.tm.list(month="2026-09")), 2)
        self.assertEqual(len(self.tm.list(category="food")), 2)
        self.assertEqual([e.date for e in self.tm.list()],
                         ["2026-08-15", "2026-09-01", "2026-09-12"])

    def test_corrupt_file_raises_storage_error(self):
        with open(self.path, "w") as f:
            f.write("{not json")
        with self.assertRaises(storage.StorageError):
            TransactionManager(self.path)


if __name__ == "__main__":
    unittest.main()
