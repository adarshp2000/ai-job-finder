from pathlib import Path
import sqlite3

DB_PATH = Path("data/jobs.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn