"""Input validation and formatting helpers."""
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

CATEGORIES = [
    "Food", "Rent", "Transport", "Education",
    "Entertainment", "Health", "Shopping", "Utilities", "Other",
]

MAX_NOTE_LENGTH = 200


class ValidationError(ValueError):
    """Raised when user input is invalid."""


def parse_date(text, today: date = None) -> date:
    """Parse YYYY-MM-DD and reject malformed or future dates."""
    today = today or date.today()
    if not isinstance(text, str) or not text.strip():
        raise ValidationError("Date is required (format YYYY-MM-DD).")
    try:
        parsed = datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(
            f"Invalid date '{text}'. Use a real date in YYYY-MM-DD format."
        ) from None
    if parsed > today:
        raise ValidationError("Date cannot be in the future.")
    return parsed


def parse_month(text) -> str:
    """Validate a month string and return it normalised as YYYY-MM."""
    if not isinstance(text, str) or not text.strip():
        raise ValidationError("Month is required (format YYYY-MM).")
    try:
        parsed = datetime.strptime(text.strip(), "%Y-%m")
    except ValueError:
        raise ValidationError(f"Invalid month '{text}'. Use YYYY-MM.") from None
    return parsed.strftime("%Y-%m")


def parse_amount(value) -> int:
    """Convert a rupee amount (e.g. '125.50') to integer paise. Must be > 0."""
    if isinstance(value, bool):
        raise ValidationError("Amount must be a number.")
    try:
        amount = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid amount '{value}'. Enter a number.") from None
    if not amount.is_finite():
        raise ValidationError("Amount must be a finite number.")
    if amount <= 0:
        raise ValidationError("Amount must be greater than zero.")
    if amount != amount.quantize(Decimal("0.01")):
        raise ValidationError("Amount can have at most 2 decimal places.")
    return int(amount * 100)


def validate_category(name) -> str:
    """Case-insensitive lookup; returns the canonical category name."""
    if isinstance(name, str):
        lookup = {c.lower(): c for c in CATEGORIES}
        key = name.strip().lower()
        if key in lookup:
            return lookup[key]
    raise ValidationError(
        f"Unknown category '{name}'. Choose from: {', '.join(CATEGORIES)}."
    )


def validate_note(note) -> str:
    note = (note or "").strip()
    if len(note) > MAX_NOTE_LENGTH:
        raise ValidationError(f"Note is too long (max {MAX_NOTE_LENGTH} characters).")
    return note


def format_paise(paise: int) -> str:
    """Format integer paise as 'Rs 1,234.50'."""
    sign = "-" if paise < 0 else ""
    paise = abs(paise)
    return f"{sign}Rs {paise // 100:,}.{paise % 100:02d}"
