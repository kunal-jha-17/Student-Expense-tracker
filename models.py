"""Data model for the expense tracker."""
from dataclasses import dataclass, asdict


@dataclass
class Expense:
    """A single expense. `amount` is stored in integer paise (1 rupee = 100 paise)."""
    id: int
    date: str          # ISO string: YYYY-MM-DD
    category: str
    amount: int        # paise
    note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        return cls(
            id=int(data["id"]),
            date=str(data["date"]),
            category=str(data["category"]),
            amount=int(data["amount"]),
            note=str(data.get("note", "")),
        )
