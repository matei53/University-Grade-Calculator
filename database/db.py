import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "app.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")
UNIVERSITIES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "universities.json")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def initialize_db():
    with get_connection() as conn:
        with open(SCHEMA_PATH, "r") as f:
            conn.executescript(f.read())
        _seed_universities(conn)

def _seed_universities(conn):
    count = conn.execute("SELECT COUNT(*) FROM universities").fetchone()[0]
    if count == 0:  # only seed if table is empty
        with open(UNIVERSITIES_PATH, "r") as f:
            universities = json.load(f)
        conn.executemany(
            "INSERT INTO universities (name) VALUES (?)",
            [(u["name"],) for u in universities]
        )