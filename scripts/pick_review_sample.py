import random
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "nifty100.db"
SCHEMA_PATH = ROOT / "db" / "schema.sql"

FALLBACK_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY,
    company_name TEXT NOT NULL,
    website TEXT,
    face_value REAL,
    book_value REAL,
    roe_percentage REAL,
    roce_percentage REAL
);

CREATE TABLE IF NOT EXISTS profit_and_loss (
    company_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    sales REAL,
    expenses REAL,
    operating_profit REAL,
    other_income REAL,
    interest REAL,
    depreciation REAL,
    profit_before_tax REAL,
    net_profit REAL,
    eps REAL,
    dividend_payout REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS balance_sheet (
    company_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    other_liabilities REAL,
    total_liabilities REAL,
    fixed_assets REAL,
    cwip REAL,
    investments REAL,
    other_asset REAL,
    total_assets REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cash_flow (
    company_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    operating_activity REAL,
    investing_activity REAL,
    financing_activity REAL,
    net_cash_flow REAL,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stock_prices (
    company_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    close_price REAL,
    volume INTEGER,
    PRIMARY KEY (company_id, date),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS documents (
    company_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    annual_report_url TEXT,
    PRIMARY KEY (company_id, year),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sector_mapping (
    company_id INTEGER PRIMARY KEY,
    sector TEXT,
    industry TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS index_history (
    company_id INTEGER NOT NULL,
    index_name TEXT NOT NULL,
    added_date TEXT,
    removed_date TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS corporate_actions (
    company_id INTEGER NOT NULL,
    action_date TEXT NOT NULL,
    action_type TEXT NOT NULL,
    ratio_or_amount TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS shareholding_pattern (
    company_id INTEGER NOT NULL,
    quarter_end TEXT NOT NULL,
    promoter_percentage REAL,
    fii_percentage REAL,
    dii_percentage REAL,
    public_percentage REAL,
    PRIMARY KEY (company_id, quarter_end),
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS load_audit (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT NOT NULL,
    file_name TEXT NOT NULL,
    rows_attempted INTEGER,
    rows_loaded INTEGER,
    rows_rejected INTEGER,
    notes TEXT
);
"""

schema_sql = ""
if SCHEMA_PATH.exists() and SCHEMA_PATH.stat().st_size > 0:
    schema_sql = SCHEMA_PATH.read_text()
else:
    schema_sql = FALLBACK_SCHEMA_SQL

with sqlite3.connect(DB_PATH) as conn:
    conn.executescript(schema_sql)
    conn.commit()

    all_ids = [row[0] for row in conn.execute("SELECT id FROM companies").fetchall()]
    if not all_ids:
        print("No companies found in the database yet.")
        raise SystemExit(0)

    random.seed(42)  # fixed seed so the sample is reproducible for the team
    sample = random.sample(all_ids, 5)

    print("Review sample (company_id):", sample)
    for cid in sample:
        name = conn.execute(
            "SELECT company_name FROM companies WHERE id=?",
            (cid,),
        ).fetchone()[0]
        print(f" {cid}: {name}")