import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def get_db():
    return sqlite3.connect(BASE_DIR / 'db_api.sqlite3')

def auth_db():
    """Compatibility alias used by views that import `auth_db`.

    Returns a sqlite3 connection to the API database.
    """
    return get_db()
