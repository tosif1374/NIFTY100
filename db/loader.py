import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(conn: sqlite3.Connection, schema_path: str):
    sql = Path(schema_path).read_text()
    conn.executescript(sql)
    conn.commit()


def load_dataframe(
    conn,
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "append",
) -> tuple[int, int]:
    """
    Insert a cleaned, validated DataFrame into the given table.
    Returns (rows_attempted, rows_loaded). Rows that violate a FK or
    PK constraint are skipped individually so one bad row doesn't
    abort the whole batch.
    """
    rows_attempted = len(df)
    rows_loaded = 0

    cols = list(df.columns)
    placeholders = ", ".join(["?"] * len(cols))
    col_list = ", ".join(cols)
    insert_sql = f"INSERT OR IGNORE INTO {table_name} ({col_list}) VALUES ({placeholders})"
    cur = conn.cursor()

    for _, row in df.iterrows():
        try:
            cur.execute(insert_sql, tuple(row[c] for c in cols))
            rows_loaded += cur.rowcount if cur.rowcount > 0 else 0
        except sqlite3.IntegrityError:
            # logged by the caller into load_audit; do not crash the batch
            continue

    conn.commit()
    return rows_attempted, rows_loaded


def record_load_audit(conn, file_name, rows_attempted, rows_loaded, notes=""):
    conn.execute(
        """INSERT INTO load_audit (run_timestamp, file_name, rows_attempted,
        rows_loaded, rows_rejected, notes)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (
            datetime.utcnow().isoformat(),
            file_name,
            rows_attempted,
            rows_loaded,
            rows_attempted - rows_loaded,
            notes,
        ),
    )
    conn.commit()