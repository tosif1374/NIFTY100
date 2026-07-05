
import pandas as pd
import numpy as np
from .db import query_df
def compute_leverage_trend(company_id: int) -> pd.DataFrame:
    """
    Yearly leverage metrics:
    - de_ratio: borrowings / equity
    - debt_to_assets: borrowings / total_assets
    - equity_ratio: equity / total_assets
    Trend: positive delta in de_ratio over 3 years signals rising leverage.
    """
    sql = """
    SELECT company_id, year,
    borrowings,
    (equity_capital + reserves) AS equity,
    total_assets,
    ROUND(borrowings / NULLIF(equity_capital + reserves, 0), 3) AS de_ratio,
    ROUND(borrowings / NULLIF(total_assets, 0), 3) AS debt_to_assets,
    ROUND((equity_capital + reserves) / NULLIF(total_assets,0), 3) AS equity_ratio
    FROM balance_sheet
    WHERE company_id = ?
    ORDER BY year
    """
    df = query_df(sql, (company_id,))
    df["de_ratio_delta_3yr"] = df["de_ratio"].diff(3).round(3)
    return df
def compute_working_capital(company_id: int) -> pd.DataFrame:
    """
    Working capital proxy (balance_sheet does not have explicit current
    assets/liabilities, so we approximate):
    - Current assets proxy: other_asset (includes receivables, inventory)
    - Current liabilities proxy: other_liabilities
    - Working capital = other_asset - other_liabilities
    - Current ratio = other_asset / other_liabilities
    """
    sql = """
    SELECT company_id, year,
    other_asset,
    other_liabilities,
    ROUND(other_asset - other_liabilities, 2) AS working_capital,
    ROUND(other_asset / NULLIF(other_liabilities, 0), 2) AS current_ratio
    FROM balance_sheet
    WHERE company_id = ?
    ORDER BY year
    """
    return query_df(sql, (company_id,))

def compute_asset_quality(company_id: int) -> pd.DataFrame:
    """
    Asset quality metrics:
    - fixed_asset_ratio: fixed_assets / total_assets (capital intensity)
    - investment_ratio: investments / total_assets
    - cwip_ratio: cwip / total_assets (high = ongoing capex cycle)
    - asset_growth_yoy: YoY % change in total_assets
    """
    sql = """
    SELECT company_id, year, total_assets,
    fixed_assets, cwip, investments,
    ROUND(fixed_assets / NULLIF(total_assets, 0), 3) AS fixed_asset_ratio,
    ROUND(investments / NULLIF(total_assets, 0), 3) AS investment_ratio,
    ROUND(cwip / NULLIF(total_assets, 0), 3) AS cwip_ratio
    FROM balance_sheet
    WHERE company_id = ?
    ORDER BY year
    """
    df = query_df(sql, (company_id,))
    df["asset_growth_yoy"] = df["total_assets"].pct_change().mul(100).round(2)
    return df
def compute_reserves_growth(company_id: int) -> pd.DataFrame:
    """
    Reserves growth is a proxy for retained earnings accumulation.
    Consistent reserves growth > 10% CAGR with low dividend payout
    indicates strong internal reinvestment.
    """
    sql = """
    SELECT company_id, year, reserves, equity_capital,
    (equity_capital + reserves) AS net_worth
    FROM balance_sheet
    WHERE company_id = ?
    ORDER BY year
    """
    df = query_df(sql, (company_id,))
    df["reserves_growth_yoy"] = df["reserves"].pct_change().mul(100).round(2)
    return df
def compute_balance_health_summary(company_id: int) -> dict:
    """
    Single-call summary for API use:
    Returns latest-year values + 3-yr trend flag for each key metric.
    """
    lev = compute_leverage_trend(company_id)
    wc = compute_working_capital(company_id)
    aq = compute_asset_quality(company_id)
    if lev.empty:
        return {"company_id": company_id, "error": "no data"}
    latest_lev = lev.iloc[-1]
    latest_wc = wc.iloc[-1] if not wc.empty else {}
    latest_aq = aq.iloc[-1] if not aq.empty else {}
    return {
        "company_id": company_id,
        "latest_year": int(latest_lev["year"]),
        "de_ratio": latest_lev["de_ratio"],
        "de_trend_3yr": latest_lev["de_ratio_delta_3yr"], # +ve = rising debt
        "current_ratio": latest_wc.get("current_ratio"),
        "fixed_asset_ratio": latest_aq.get("fixed_asset_ratio"),
        "cwip_ratio": latest_aq.get("cwip_ratio"),
        "asset_growth_yoy": latest_aq.get("asset_growth_yoy"),
    }
