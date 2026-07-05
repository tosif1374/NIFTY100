import pandas as pd
import numpy as np
from .db import query_df
def cagr(start_value: float, end_value: float, n_years: int) -> float | None:
    """
Compound Annual Growth Rate.
Returns None if inputs are non-positive or n_years < 1.
Formula: (end/start)^(1/n) - 1
"""
    if n_years < 1 or start_value is None or end_value is None:
        return None
    if start_value <= 0 or end_value <= 0:
        return None
    return round((end_value / start_value) ** (1 / n_years) - 1, 4)
def _pnl(company_id: int) -> pd.DataFrame:
    """Fetch full P&L for a company ordered by year."""
    return query_df(
"""SELECT * FROM profit_and_loss
WHERE company_id = ? ORDER BY year""",
(company_id,)
)
def compute_sales_cagr(company_id: int, years: int = 5) -> dict:
    """
Sales CAGR over the most recent N years.
Returns dict: {company_id, years, start_year, end_year,
start_sales, end_sales, sales_cagr}
"""
    df = _pnl(company_id).dropna(subset=["sales"])
    if len(df) < 2:
        return {}
    df = df.tail(years + 1) # need n+1 rows for n-year CAGR
    n = len(df) - 1
    result = {
        "company_id": company_id,
        "years": n,
        "start_year": int(df.iloc[0]["year"]),
        "end_year": int(df.iloc[-1]["year"]),
        "start_sales": float(df.iloc[0]["sales"]),
        "end_sales": float(df.iloc[-1]["sales"]),
        "sales_cagr": cagr(df.iloc[0]["sales"], df.iloc[-1]["sales"], n),
    }
    return result
def compute_profit_cagr(company_id: int, years: int = 5) -> dict:
    """Net profit CAGR over most recent N years.
Returns None if start or end net_profit is negative
(CAGR is undefined for sign changes)."""
    df = _pnl(company_id).dropna(subset=["net_profit"])
    if len(df) < 2:
        return {}
    df = df.tail(years + 1)
    n = len(df) - 1
    return {
        "company_id": company_id,
        "years": n,
        "start_year": int(df.iloc[0]["year"]),
        "end_year": int(df.iloc[-1]["year"]),
        "start_profit": float(df.iloc[0]["net_profit"]),
        "end_profit": float(df.iloc[-1]["net_profit"]),
        "profit_cagr": cagr(df.iloc[0]["net_profit"], df.iloc[-1]["net_profit"], n),
    }


def compute_margin_series(company_id: int) -> pd.DataFrame:
    """
    Returns yearly margin table:
    - operating_margin = operating_profit / sales
    - net_margin = net_profit / sales
    - ebitda_margin = (operating_profit + depreciation) / sales
    """
    sql = """
    SELECT company_id, year, sales, operating_profit,
    net_profit, depreciation,
    ROUND(100.0 * operating_profit / NULLIF(sales, 0), 2) AS operating_margin,
    ROUND(100.0 * net_profit / NULLIF(sales, 0), 2) AS net_margin,
    ROUND(100.0 * (operating_profit + depreciation)
    / NULLIF(sales, 0), 2) AS ebitda_margin
    FROM profit_and_loss
    WHERE company_id = ?
    ORDER BY year
    """
    return query_df(sql, (company_id,))
def compute_eps_trend(company_id: int) -> pd.DataFrame:
    """
    Returns EPS per year with YoY growth % and 5-yr CAGR.
    Also flags potential unit-inconsistency: if any year's EPS differs from
    the net_profit/shares_estimate by more than 10x, sets eps_unit_flag=True.
    """
    sql = """
    SELECT p.company_id, p.year, p.eps, p.net_profit,
    ROUND(b.equity_capital / NULLIF(c.face_value, 0), 0) AS shares_cr,
    ROUND(p.net_profit
    / NULLIF(b.equity_capital / NULLIF(c.face_value, 0), 0),
    2) AS eps_computed
    FROM profit_and_loss p
    JOIN balance_sheet b USING (company_id, year)
    JOIN companies c ON c.id = p.company_id
    WHERE p.company_id = ?
    ORDER BY p.year
    """
    df = query_df(sql, (company_id,))
    # YoY EPS growth
    df["eps_yoy_pct"] = df["eps"].pct_change().mul(100).round(2)
    # Unit flag: reported EPS more than 10x different from computed EPS
    df["eps_unit_flag"] = (
        (df["eps"].notna() & df["eps_computed"].notna()) &
        ((df["eps"] / df["eps_computed"].replace(0, pd.NA)).abs() > 10)
    )
    return df
def compute_dividend_stability(company_id: int) -> dict:
    """
    Dividend payout stability over available years.
    Returns: mean, std, coefficient_of_variation of dividend_payout %.
    A CV < 0.3 is considered stable.
    """
    df = query_df(
        "SELECT year, dividend_payout FROM profit_and_loss "
        "WHERE company_id = ? AND dividend_payout IS NOT NULL ORDER BY year",
        (company_id,))
    if df.empty:
        return {"company_id": company_id, "div_mean": None, "div_std": None, "div_cv": None}
    return {
        "company_id": company_id,
        "div_years": len(df),
        "div_mean": round(float(df["dividend_payout"].mean()), 2),
        "div_std": round(float(df["dividend_payout"].std()), 2),
        "div_cv": round(float(df["dividend_payout"].std()
        / df["dividend_payout"].mean()), 3)
        if df["dividend_payout"].mean() != 0 else None,
    }