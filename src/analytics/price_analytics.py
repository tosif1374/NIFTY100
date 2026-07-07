import pandas as pd
import numpy as np
from .db import query_df
RISK_FREE_RATE_ANNUAL = 0.065 # 6.5% — approximate RBI repo rate 2020-2024
TRADING_MONTHS = 12 # monthly data
def _prices(company_id: int) -> pd.DataFrame:
    """Fetch monthly close prices, parse date, sort ascending."""
    df = query_df(
        """SELECT company_id, date, close_price, volume
        FROM stock_prices WHERE company_id = ?
        ORDER BY date""",
        (company_id,))
    df["date"] = pd.to_datetime(df["date"])
    return df
def compute_monthly_returns(company_id: int) -> pd.DataFrame:
    """
    Simple monthly return: (P_t - P_{t-1}) / P_{t-1}
    Log return: ln(P_t / P_{t-1})
    """
    df = _prices(company_id)
    df = load_price_data(company_id)

    df["close_price"] = pd.to_numeric(
    df["close_price"],
    errors="coerce"
)

    df["simple_return"] = (
    df["close_price"]
    .pct_change()
    .round(6)
)
    df["log_return"] = np.log(df["close_price"] / df["close_price"].shift(1)).round(6)
    return df
def compute_rolling_sharpe(company_id: int, window: int = 12) -> pd.DataFrame:
    """
    Rolling Sharpe ratio over a trailing window of monthly returns.
    Annualised: Sharpe = (mean_monthly_return - monthly_rfr) / std_monthly_return
    * sqrt(12)
    Monthly risk-free rate = RISK_FREE_RATE_ANNUAL / 12
    """
    df = compute_monthly_returns(company_id)
    rfr_monthly = RISK_FREE_RATE_ANNUAL / TRADING_MONTHS
    excess = df["simple_return"] - rfr_monthly
    df["rolling_sharpe"] = (
        excess.rolling(window).mean() / excess.rolling(window).std()
        * np.sqrt(TRADING_MONTHS)
    ).round(3)
    return df
def compute_max_drawdown(company_id: int) -> dict:
    """
    Maximum drawdown over the full price series.
    Drawdown at t = (P_t - running_max) / running_max
    Max drawdown = minimum of all drawdown values.
    """
    df = _prices(company_id)
    if df.empty:
        return {"company_id": company_id, "max_drawdown_pct": None}
    roll_max = df["close_price"].cummax()
    drawdown = (df["close_price"] - roll_max) / roll_max
    max_dd_idx = drawdown.idxmin()
    return {
        "company_id": company_id,
        "max_drawdown_pct": round(float(drawdown.min()) * 100, 2),
        "drawdown_trough_date": str(df.loc[max_dd_idx, "date"].date())
        if max_dd_idx is not None else None,
    }
def compute_annualised_return(company_id: int) -> dict:
    """
    Annualised return from first to last available price (CAGR of price).
    Also returns total_return and CAGR vs Nifty-100 benchmark
    (benchmark must be pre-loaded as company_id 0 if desired).
    """
    df = _prices(company_id).dropna(subset=["close_price"])
    if len(df) < 2:
        return {"company_id": company_id, "annualised_return": None}
    p0, pt = df.iloc[0]["close_price"], df.iloc[-1]["close_price"]
    n_months = len(df) - 1
    total_return = (pt - p0) / p0
    ann_return = (1 + total_return) ** (12 / n_months) - 1
    return {
        "company_id": company_id,
        "start_date": str(df.iloc[0]["date"].date()),
        "end_date": str(df.iloc[-1]["date"].date()),
        "n_months": n_months,
        "total_return_pct": round(total_return * 100, 2),
        "annualised_return_pct": round(ann_return * 100, 2),
    }
def find_sparse_price_coverage(min_months: int = 24) -> pd.DataFrame:
    """
    Sprint 1 carry-over: identifies companies with fewer than min_months
    of stock price data so they can be prioritised for backfilling.
    """
    sql = """
    SELECT c.id AS company_id, c.company_name,
    COUNT(sp.date) AS months_available
    FROM companies c
    LEFT JOIN stock_prices sp ON sp.company_id = c.id
    GROUP BY c.id, c.company_name
    HAVING COUNT(sp.date) < ?
    ORDER BY months_available ASC
    """
    return query_df(sql, (min_months,))
def compute_price_summary(company_id: int) -> dict:
    """API-ready summary: latest price, 12m return, max drawdown, latest Sharpe."""
    df = compute_rolling_sharpe(company_id, window=12)
    if df.empty:
        return {"company_id": company_id, "error": "no data"}
    ann = compute_annualised_return(company_id)
    mdd = compute_max_drawdown(company_id)
    df_12m = df.tail(12)
    return {
        "company_id": company_id,
        "latest_price": float(df.iloc[-1]["close_price"]),
        "latest_date": str(df.iloc[-1]["date"].date()),
        "return_12m_pct": round(float(df_12m.iloc[-1]["close_price"] /
        df_12m.iloc[0]["close_price"] - 1) * 100, 2)
        if len(df_12m) > 1 else None,
        "annualised_return_pct": ann.get("annualised_return_pct"),
        "max_drawdown_pct": mdd.get("max_drawdown_pct"),
        "latest_rolling_sharpe": float(df.iloc[-1]["rolling_sharpe"])
        if pd.notna(df.iloc[-1]["rolling_sharpe"]) else None,
    }
