import sqlite3
import os
from functools import lru_cache
DB_PATH = os.getenv("DB_PATH", "./db/nifty100.db")
def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open a read-only connection to nifty100.db with FK enforcement."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row # column access by name
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
def query_df(sql: str, params=(), db_path: str = DB_PATH):
    """Execute a SELECT and return a pandas DataFrame directly."""
    import pandas as pd
    with get_connection(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=params)