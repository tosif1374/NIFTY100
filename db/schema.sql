PRAGMA foreign_keys = ON;

-- 1. Hub table -------------------------------------------------------------
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

-- 4. Cash Flow (time series) -------------------------------------------------
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
date TEXT NOT NULL, -- ISO format YYYY-MM-DD
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
index_name TEXT NOT NULL, -- e.g. 'NIFTY 100'
added_date TEXT,
removed_date TEXT,
FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS corporate_actions (
company_id INTEGER NOT NULL,
action_date TEXT NOT NULL,
action_type TEXT NOT NULL, -- 'split' | 'bonus' | 'dividend'
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
-- Helpful indexes for the analytics layer (Sprint 2) --------------------------
CREATE INDEX IF NOT EXISTS idx_pnl_year ON profit_and_loss(year);
CREATE INDEX IF NOT EXISTS idx_bs_year ON balance_sheet(year);
CREATE INDEX IF NOT EXISTS idx_cf_year ON cash_flow(year);
CREATE INDEX IF NOT EXISTS idx_sp_date ON stock_prices(date);