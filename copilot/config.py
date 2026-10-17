"""Runtime configuration. Everything dataset-specific comes from .env or the data itself."""
import os
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DB_PATH = Path(os.getenv("DB_PATH", ROOT / "data" / "data.db"))
MEMORY_DB = Path(os.getenv("MEMORY_DB", ROOT / "data" / "memory.db"))
TODAY = date.fromisoformat(os.getenv("TODAY", "2026-10-17"))


def data_dirs() -> list[Path]:
    raw = os.getenv("DATA_DIRS", "")
    out = []
    for p in (x.strip() for x in raw.split(",") if x.strip()):
        path = Path(p)
        out.append(path if path.is_absolute() else (ROOT / path).resolve())
    return out
