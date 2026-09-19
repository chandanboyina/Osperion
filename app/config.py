from __future__ import annotations
import os
from pathlib import Path

APP_NAME = "OSPERION"
VERSION = "0.5.0"
DEFAULT_RETENTION_DAYS = 30


def data_dir() -> Path:
    root = os.getenv("OSPERION_DATA_DIR") or os.getenv("TRACELENS_DATA_DIR")
    p = Path(root).expanduser() if root else Path.home() / ".osperion"
    p.mkdir(parents=True, exist_ok=True)
    return p


def db_path() -> Path:
    return data_dir() / "osperion.sqlite3"


def retention_path() -> Path:
    return data_dir() / "retention_days.txt"


def get_retention_days() -> int:
    try:
        value = int(retention_path().read_text().strip())
        return max(1, min(value, 3650))
    except Exception:
        return DEFAULT_RETENTION_DAYS


def set_retention_days(days: int) -> int:
    days = max(1, min(int(days), 3650))
    retention_path().write_text(str(days), encoding="utf-8")
    return days
