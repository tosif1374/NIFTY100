import pandas as pd
import numpy as np
from .db import query_df
def compute_fcf(company_id: int) -> pd.DataFrame:
    """
    Free Cash Flow = Operating Cash Flow - Capital Expenditure (Capex)
    Capex proxy = increase in fixed_assets + cwip (from balance_sheet YoY delta)
    Note: Screener's cash_flow table uses the indirect method, so
    operating_activity already excludes capex.
    """
    cf_sql = """
    SELECT company_id, year,
    operating_activity, investing_activity, financing_activity,
    net_cash_flow
    FROM cash_flow
    WHERE company_id = ? ORDER BY year
    """
    bs_sql = """
    SELECT company_id, year,
    fixed_assets + cwip AS gross_fixed
    FROM balance_sheet
    WHERE company_id = ? ORDER BY year
    """
    cf = query_df(cf_sql, (company_id,))
    bs = query_df(bs_sql, (company_id,))
    bs["capex"] = bs["gross_fixed"].diff() # positive = capex outflow
    merged = cf.merge(bs[["year","capex"]], on="year", how="left")
    merged["fcf"] = merged["operating_activity"] - merged["capex"].clip(lower=0)
    merged["fcf"] = merged["fcf"].round(2)
    return merged
def compute_cfo_quality(company_id: int) -> pd.DataFrame:
    """
    CFO/Net Profit ratio: the primary cash quality indicator.
    > 1.0 — Excellent: cash exceeds reported profit (good accrual quality)
    0.7-1.0 — Acceptable
    < 0.7 — Warning: earnings may not be cash-backed
    < 0 — Red flag: negative operating cash flow despite positive profit
    """
    sql = """
    SELECT cf.company_id, cf.year,
    cf.operating_activity AS cfo,
    p.net_profit,
    ROUND(cf.operating_activity / NULLIF(p.net_profit, 0), 3) AS cfo_np_ratio
    FROM cash_flow cf
    JOIN profit_and_loss p USING (company_id, year)
    WHERE cf.company_id = ?
    ORDER BY cf.year
    """
    df = query_df(sql, (company_id,))
    # Quality flag
    conditions = [
        df["cfo_np_ratio"] >= 1.0,
        df["cfo_np_ratio"] >= 0.7,
        df["cfo_np_ratio"] >= 0.0,
    ]
    choices = ["excellent", "acceptable", "warning"]
    df["cfo_quality"] = np.select(conditions, choices, default="red_flag")
    return df
def compute_capex_intensity(company_id: int) -> pd.DataFrame:
    """
    Capex as % of sales: high capex-intensity industries (steel, power,
    cement, telecom) will consistently show 15-30%+ here.
    Also computes capex/CFO to see how much operating cash is re-invested.
    """
    bs_sql = """
    SELECT company_id, year, fixed_assets + cwip AS gross_fixed
    FROM balance_sheet WHERE company_id = ? ORDER BY year
    """
    pnl_sql = """
    SELECT year, sales FROM profit_and_loss WHERE company_id = ? ORDER BY year
    """
    cf_sql = """
    SELECT year, operating_activity AS cfo
    FROM cash_flow WHERE company_id = ? ORDER BY year
    """
    bs = query_df(bs_sql, (company_id,))
    pnl = query_df(pnl_sql, (company_id,))
    cf = query_df(cf_sql, (company_id,))
    bs["capex"] = bs["gross_fixed"].diff().clip(lower=0)
    df = bs[["year","capex"]].merge(pnl, on="year").merge(cf, on="year")
    df["capex_pct_sales"] = (df["capex"] / df["sales"].replace(0, pd.NA) * 100).round(2)
    df["capex_pct_cfo"] = (df["capex"] / df["cfo"].replace(0, pd.NA) * 100).round(2)
    df.insert(0, "company_id", company_id)
    return df
def compute_cashflow_summary(company_id: int) -> dict:
    """Sprint 3 API-ready summary: latest year FCF, CFO quality flag, and 3-yr avg."""
    fcf = compute_fcf(company_id)
    qual = compute_cfo_quality(company_id)
    if fcf.empty:
        return {"company_id": company_id, "error": "no data"}
    return {
        "company_id": company_id,
        "latest_year": int(fcf.iloc[-1]["year"]),
        "latest_fcf": float(fcf.iloc[-1]["fcf"]),
        "fcf_3yr_avg": round(float(fcf.tail(3)["fcf"].mean()), 2),
        "latest_cfo": float(fcf.iloc[-1]["operating_activity"]),
        "latest_cfo_np_ratio": float(qual.iloc[-1]["cfo_np_ratio"]) if not qual.empty else None,
        "cfo_quality_flag": qual.iloc[-1]["cfo_quality"] if not qual.empty else None,
    }
