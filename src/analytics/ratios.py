import pandas as pd
import numpy as np
from .db import query_df

def compute_roe(company_id: int) -> pd.DataFrame:
    """
ROE = Net Profit / Shareholders Equity
Shareholders Equity = equity_capital + reserves (from balance_sheet)
"""
    sql = """
SELECT p.company_id, p.year,
p.net_profit,
(b.equity_capital + b.reserves) AS shareholders_equity,
ROUND(
100.0 * p.net_profit / NULLIF(b.equity_capital + b.reserves, 0),
2) AS roe_pct
FROM profit_and_loss p
JOIN balance_sheet b USING (company_id, year)
WHERE p.company_id = ?
ORDER BY p.year
"""
    return query_df(sql, (company_id,))
# nn Return on Capital Employed 
def compute_roce(company_id: int) -> pd.DataFrame:
    """
ROCE = EBIT / Capital Employed
EBIT = operating_profit + other_income - depreciation (approx)
Capital Employed = total_assets - other_liabilities (current liabilities proxy)
"""
    sql = """
SELECT p.company_id, p.year,
(p.operating_profit + p.other_income - p.depreciation) AS ebit,
(b.total_assets - b.other_liabilities) AS cap_employed,
ROUND(
100.0 * (p.operating_profit + p.other_income - p.depreciation)
/ NULLIF(b.total_assets - b.other_liabilities, 0),
2) AS roce_pct
FROM profit_and_loss p
JOIN balance_sheet b USING (company_id, year)
WHERE p.company_id = ?
ORDER BY p.year
"""
    return query_df(sql, (company_id,))
# nn Debt-to-Equity 
def compute_debt_to_equity(company_id: int) -> pd.DataFrame:
    """D/E = total borrowings / (equity_capital + reserves)"""
    sql = """
SELECT company_id, year,
borrowings,
(equity_capital + reserves) AS equity,
ROUND(borrowings / NULLIF(equity_capital + reserves, 0), 2) AS de_ratio
FROM balance_sheet
WHERE company_id = ?
ORDER BY year
"""
    return query_df(sql, (company_id,))
# nn Interest Coverage
def compute_interest_coverage(company_id: int) -> pd.DataFrame:
    """ICR = EBIT / Interest. ICR < 1.5 is a stress signal."""
    sql = """
SELECT company_id, year,
(operating_profit + other_income) AS ebit,
interest,
ROUND(
(operating_profit + other_income) / NULLIF(interest, 0),
2) AS icr
FROM profit_and_loss
WHERE company_id = ?
ORDER BY year
"""
    return query_df(sql, (company_id,))
# nn Price-to-Book 
def compute_price_to_book(company_id: int) -> pd.DataFrame:
    """
P/B = Close Price / Book Value per Share
Book Value per Share = (equity_capital + reserves) / shares_outstanding
Shares outstanding approximated as: equity_capital / face_value
Uses December closing price as the year-end price proxy.
"""
    sql = """
SELECT b.company_id, b.year,
sp.close_price,
(b.equity_capital + b.reserves) AS equity,
c.face_value,
ROUND(b.equity_capital / NULLIF(c.face_value, 0), 0) AS shares_cr,
ROUND(
(b.equity_capital + b.reserves)
/ NULLIF(b.equity_capital / NULLIF(c.face_value, 0), 0),
2) AS book_value_per_share,
ROUND(
sp.close_price
/ NULLIF(
(b.equity_capital + b.reserves)
/ NULLIF(b.equity_capital / NULLIF(c.face_value,0), 0),
0),
2) AS pb_ratio
FROM balance_sheet b
JOIN companies c ON c.id = b.company_id
JOIN (
SELECT company_id,
CAST(strftime('%Y', date) AS INT) AS price_year,
close_price
FROM stock_prices
WHERE strftime('%m', date) = '12' -- December year-end price
) sp ON sp.company_id = b.company_id AND sp.price_year = b.year
WHERE b.company_id = ?
ORDER BY b.year
"""
    return query_df(sql, (company_id,))
# nn Batch: all ratios for one company, one DataFrame 
def compute_all_ratios(company_id: int) -> pd.DataFrame:
    """Merge ROE, ROCE, D/E, ICR into one wide DataFrame keyed by (company_id, year)."""
    roe = compute_roe(company_id)[["company_id","year","roe_pct"]]
    roce = compute_roce(company_id)[["company_id","year","roce_pct"]]
    de = compute_debt_to_equity(company_id)[["company_id","year","de_ratio"]]
    icr = compute_interest_coverage(company_id)[["company_id","year","icr"]]
    base = roe.merge(roce, on=["company_id","year"], how="outer")
    base = base.merge(de, on=["company_id","year"], how="outer")
    base = base.merge(icr, on=["company_id","year"], how="outer")
    return base.sort_values("year")
