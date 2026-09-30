"""JSON / CSV input-output."""
import csv
import json
import os
from pathlib import Path

from models import Expense

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXPENSES_PATH = DATA_DIR / "expenses.json"
BUDGETS_PATH = DATA_DIR / "budgets.json"


class StorageError(Exception):
    """Raised when data cannot be read or written."""


def _read_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    try:
        text = p.read_text(encoding="utf-8")
        if not text.strip():
            return default
        return json.loads(text)
    except (OSError, json.JSONDecodeError) as exc:
        raise StorageError(f"Could not read {p}: {exc}") from exc


def _write_json(path, data):
    p = Path(path)
    tmp = p.with_name(p.name + ".tmp")
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, p)  # atomic: never leaves a half-written file
    except OSError as exc:
        raise StorageError(f"Could not write {p}: {exc}") from exc


def load_expenses(path=EXPENSES_PATH) -> list:
    data = _read_json(path, [])
    if not isinstance(data, list):
        raise StorageError(f"{path} must contain a JSON list.")
    try:
        return [Expense.from_dict(item) for item in data]
    except (KeyError, TypeError, ValueError) as exc:
        raise StorageError(f"Corrupt expense record in {path}: {exc}") from exc


def save_expenses(expenses, path=EXPENSES_PATH):
    _write_json(path, [e.to_dict() for e in expenses])


def load_budgets(path=BUDGETS_PATH) -> dict:
    data = _read_json(path, {})
    if not isinstance(data, dict):
        raise StorageError(f"{path} must contain a JSON object.")
    try:
        return {str(k): int(v) for k, v in data.items()}
    except (TypeError, ValueError) as exc:
        raise StorageError(f"Corrupt budget data in {path}: {exc}") from exc


def save_budgets(budgets: dict, path=BUDGETS_PATH):
    _write_json(path, budgets)


def export_csv(expenses, path, month: str = None) -> int:
    """Write expenses (optionally only one YYYY-MM month) to CSV. Returns row count."""
    rows = [e for e in expenses if month is None or e.date[:7] == month]
    rows.sort(key=lambda e: (e.date, e.id))
    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "date", "category", "amount_rupees", "note"])
            for e in rows:
                writer.writerow(
                    [e.id, e.date, e.category, f"{e.amount // 100}.{e.amount % 100:02d}", e.note]
                )
    except OSError as exc:
        raise StorageError(f"Could not write {p}: {exc}") from exc
    return len(rows)
