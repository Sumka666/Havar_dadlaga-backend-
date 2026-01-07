import sqlite3
from pathlib import Path
from django.conf import settings

BASE = Path(settings.BASE_DIR)

def auth_db():
    return sqlite3.connect(BASE / 'db' / 'auth.db')

def restaurant_db():
    return sqlite3.connect(BASE / 'db' / 'restaurant.db')
