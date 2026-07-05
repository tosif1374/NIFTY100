
import pandas as pd
import numpy as np
from .db import query_df
from .ratios import compute_all_ratios
from .pnl_trends import compute_margin_series
def get_sector_peers(company_id: int) -> list[int]:
    """Return list of company_ids in the same sector as the given company."""
    df = query_df(
        """SELECT s.company_id FROM sector_mapping s
        WHERE s.sector = (
            SELECT sector FROM sector_mapping WHERE company_id = ?
        )""",
        (company_id,))
    return list(df["company_id"].astype(int))
def compute_sector_averages(sector: str, year: int) -> pd.DataFrame:
    """
    Sector-level averages for a given fiscal year.
    Returns ROE, ROCE, D/E, operating_margin for all companies in the sector.
    """
    sql = """
    SELECT c.id AS company_id, c.company_name, s.sector, s.industry,
    ROUND(100.0 * p.net_profit
    / NULLIF(b.equity_capital + b.reserves, 0), 2) AS roe_pct,
    ROUND(100.0 * (p.operating_profit + p.other_income - p.depreciation)
    / NULLIF(b.total_assets - b.other_liabilities, 0), 2) AS roce_pct,
    ROUND(b.borrowings
    / NULLIF(b.equity_capital + b.reserves, 0), 3) AS de_ratio,
    ROUND(100.0 * p.operating_profit
    / NULLIF(p.sales, 0), 2) AS op_margin_pct,
    ROUND(100.0 * p.net_profit
    / NULLIF(p.sales, 0), 2) AS net_margin_pct
    FROM companies c
    JOIN sector_mapping s ON s.company_id = c.id
    JOIN profit_and_loss p ON p.company_id = c.id AND p.year = ?
    JOIN balance_sheet b ON b.company_id = c.id AND b.year = ?
    WHERE s.sector = ?
    ORDER BY roe_pct DESC
    """
    return query_df(sql, (year, year, sector))
def compute_sector_summary(sector: str, year: int) -> pd.DataFrame:
    """
    Aggregated stats per sector: mean, median, min, max for key metrics.
    Returns a single-row DataFrame.
    """
    df = compute_sector_averages(sector, year)
    if df.empty:
        return pd.DataFrame()
    summary = {
        "sector": sector,
        "year": year,
        "n_companies": len(df),
        "roe_mean": round(df["roe_pct"].mean(), 2),
        "roe_median": round(df["roe_pct"].median(), 2),
        "roce_mean": round(df["roce_pct"].mean(), 2),
        "de_mean": round(df["de_ratio"].mean(), 3),
        "op_margin_mean": round(df["op_margin_pct"].mean(), 2),
    }
    return pd.DataFrame([summary])
def compute_peer_ranking(company_id: int, year: int) -> dict:
    """
    Rank a company within its sector peers on ROE and ROCE for a given year.
    Returns rank (1 = best), percentile, and total peers.
    """
    sector_row = query_df(
        "SELECT sector FROM sector_mapping WHERE company_id = ?", (company_id,))
    if sector_row.empty:
        return {"company_id": company_id, "error": "not in sector_mapping"}
    sector = sector_row.iloc[0]["sector"]
    df = compute_sector_averages(sector, year).reset_index(drop=True)
    if df.empty:
        return {"company_id": company_id, "error": "no sector data"}
    df_sorted_roe = df.sort_values("roe_pct", ascending=False).reset_index(drop=True)
    df_sorted_roe["roe_rank"] = df_sorted_roe.index + 1
    row = df_sorted_roe[df_sorted_roe["company_id"] == company_id]
    if row.empty:
        return {"company_id": company_id, "error": "company not in sector for year"}
    r = row.iloc[0]
    n = len(df)
    return {
        "company_id": company_id,
        "sector": sector,
        "year": year,
        "n_peers": n,
        "roe_pct": r["roe_pct"],
        "roe_rank": int(r["roe_rank"]),
        "roe_percentile": round((1 - (int(r["roe_rank"]) - 1) / n) * 100, 1),
        "roce_pct": r["roce_pct"],
        "op_margin_pct": r["op_margin_pct"],
    }
def compute_all_sectors_latest(latest_year: int = 2024) -> pd.DataFrame:
    """
    Cross-sector comparison table for the latest year.
    Used by Sprint 3's /api/sectors endpoint.
    """
    sectors = query_df("SELECT DISTINCT sector FROM sector_mapping ORDER BY sector")
    frames = []
    for sector in sectors["sector"].tolist():
        summary = compute_sector_summary(sector, latest_year)
        if not summary.empty:
            frames.append(summary)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
