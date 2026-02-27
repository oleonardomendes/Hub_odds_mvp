import os
from .db import get_db

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")

def ensure_schema():
    with get_db() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          filename TEXT NOT NULL UNIQUE,
          applied_at TEXT NOT NULL
        );
        """)

        applied = set(r["filename"] for r in con.execute("SELECT filename FROM schema_migrations").fetchall())

        if not os.path.isdir(MIGRATIONS_DIR):
            return

        files = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql")])
        for f in files:
            if f in applied:
                continue
            path = os.path.join(MIGRATIONS_DIR, f)
            sql = open(path, "r", encoding="utf-8").read()
            con.executescript(sql)
            con.execute("INSERT INTO schema_migrations(filename, applied_at) VALUES(?, datetime('now'))", (f,))