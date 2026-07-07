import pandas as pd
import numpy as np

from .db import query_df
from .ratios import compute_all_ratios
from .pnl_trends import compute_margin_series


def _coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Safely convert columns to numeric.
    Prevents SQLite/object dtype issues during calculations.
    """
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def get_sector_peers(company_id: int) -> list[int]:
    """
    Return all company_ids belonging to the same sector.
    """
    df = query_df(
        """
        SELECT company_id
        FROM sector_mapping
        WHERE sector = (
            SELECT sector
            FROM sector_mapping
            WHERE company_id = ?
        )
        """,
        (company_id,),
    )

    if df.empty:
        return []

    return df["company_id"].dropna().astype(int).tolist()


def compute_sector_averages(sector: str, year: int) -> pd.DataFrame:
    """
    Sector-level metrics for all companies in a sector for a given year.
    """

    sql = """
    SELECT
        c.id AS company_id,
        c.company_name,
        s.sector,
        s.industry,

        ROUND(
            100.0 * p.net_profit /
            NULLIF(b.equity_capital + b.reserves, 0),
            2
        ) AS roe_pct,

        ROUND(
            100.0 *
            (p.operating_profit + p.other_income - p.depreciation) /
            NULLIF(b.total_assets - b.other_liabilities, 0),
            2
        ) AS roce_pct,

        ROUND(
            b.borrowings /
            NULLIF(b.equity_capital + b.reserves, 0),
            3
        ) AS de_ratio,

        ROUND(
            100.0 * p.operating_profit /
            NULLIF(p.sales, 0),
            2
        ) AS op_margin_pct,

        ROUND(
            100.0 * p.net_profit /
            NULLIF(p.sales, 0),
            2
        ) AS net_margin_pct

    FROM companies c

    JOIN sector_mapping s
        ON s.company_id = c.id

    JOIN profit_and_loss p
        ON p.company_id = c.id
        AND p.year = ?

    JOIN balance_sheet b
        ON b.company_id = c.id
        AND b.year = ?

    WHERE s.sector = ?

    ORDER BY roe_pct DESC
    """

    df = query_df(sql, (year, year, sector))

    numeric_cols = [
        "roe_pct",
        "roce_pct",
        "de_ratio",
        "op_margin_pct",
        "net_margin_pct",
    ]

    return _coerce_numeric(df, numeric_cols)


def compute_sector_summary(sector: str, year: int) -> pd.DataFrame:
    """
    Aggregated sector statistics.
    Returns a single-row dataframe.
    """

    df = compute_sector_averages(sector, year)

    if df.empty:
        return pd.DataFrame()

    numeric_cols = [
        "roe_pct",
        "roce_pct",
        "de_ratio",
        "op_margin_pct",
    ]

    df = _coerce_numeric(df, numeric_cols)

    summary = {
        "sector": sector,
        "year": year,
        "n_companies": int(len(df)),
        "roe_mean": round(df["roe_pct"].mean(), 2),
        "roe_median": round(df["roe_pct"].median(), 2),
        "roce_mean": round(df["roce_pct"].mean(), 2),
        "de_mean": round(df["de_ratio"].mean(), 3),
        "op_margin_mean": round(df["op_margin_pct"].mean(), 2),
    }

    return pd.DataFrame([summary])


def compute_peer_ranking(company_id: int, year: int) -> dict:
    """
    Rank a company among sector peers based on ROE.
    """

    sector_row = query_df(
        """
        SELECT sector
        FROM sector_mapping
        WHERE company_id = ?
        """,
        (company_id,),
    )

    if sector_row.empty:
        return {
            "company_id": company_id,
            "error": "Company not found in sector_mapping",
        }

    sector = sector_row.iloc[0]["sector"]

    df = compute_sector_averages(sector, year)

    if df.empty:
        return {
            "company_id": company_id,
            "error": "No sector data found",
        }

    df = _coerce_numeric(
        df,
        [
            "roe_pct",
            "roce_pct",
            "op_margin_pct",
        ],
    )

    df = (
        df.sort_values("roe_pct", ascending=False)
        .reset_index(drop=True)
    )

    df["roe_rank"] = df.index + 1

    row = df[df["company_id"] == company_id]

    if row.empty:
        return {
            "company_id": company_id,
            "error": "Company not present in sector ranking",
        }

    row = row.iloc[0]

    total_peers = len(df)

    return {
        "company_id": int(company_id),
        "sector": sector,
        "year": int(year),
        "n_peers": int(total_peers),
        "roe_pct": (
            None
            if pd.isna(row["roe_pct"])
            else float(row["roe_pct"])
        ),
        "roe_rank": int(row["roe_rank"]),
        "roe_percentile": round(
            (1 - (int(row["roe_rank"]) - 1) / total_peers) * 100,
            1,
        ),
        "roce_pct": (
            None
            if pd.isna(row["roce_pct"])
            else float(row["roce_pct"])
        ),
        "op_margin_pct": (
            None
            if pd.isna(row["op_margin_pct"])
            else float(row["op_margin_pct"])
        ),
    }


def compute_all_sectors_latest(latest_year=None):
    if latest_year is None:
        latest_year = int(
            query_df(
                "SELECT MAX(year) AS latest_year FROM profit_and_loss"
            ).iloc[0]["latest_year"]
        )

    sectors = query_df(
        "SELECT DISTINCT sector FROM sector_mapping ORDER BY sector"
    )

    rows = []

    for sector in sectors["sector"]:
        df = compute_sector_averages(sector, latest_year)

        if df.empty:
            continue

        rows.append(
            {
                "sector": sector,
                "year": latest_year,
                "n_companies": len(df),
                "roe_mean": round(df["roe_pct"].mean(), 2),
                "roe_median": round(df["roe_pct"].median(), 2),
                "roce_mean": round(df["roce_pct"].mean(), 2),
                "de_mean": round(df["de_ratio"].mean(), 3),
                "op_margin_mean": round(df["op_margin_pct"].mean(), 2),
            }
        )

    return pd.DataFrame(rows)