import sqlite3
from contextlib import contextmanager
from .config import settings

def connect():
    con = sqlite3.connect(settings.db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON;")
    return con

@contextmanager
def get_db():
    con = connect()
    try:
        yield con
        con.commit()
    finally:
        con.close()
