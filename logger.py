"""Central logging setup (writes to logs/app.log)."""
import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
LOG_FILE = LOG_DIR / "app.log"


def get_logger(name: str = "expense_tracker") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    try:
        LOG_DIR.mkdir(exist_ok=True)
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
    except OSError:  # read-only folder etc. -> never crash because of logging
        handler = logging.NullHandler()
    logger.addHandler(handler)
    return logger
