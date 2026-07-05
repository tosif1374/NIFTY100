import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ..deps import CurrentUser, DbDep, SnapshotDir
from ..schemas import CAGRSummary, CompanyList, MarginYear, PnLResponse, RatioYear, RatiosResponse

router = APIRouter()


@router.get("/companies", response_model=list[CompanyList])
async def list_companies(
    db: DbDep,
    _: CurrentUser,
    sector: str | None = Query(None, description="Filter by sector name"),
):
    """List all Nifty 100 companies with optional sector filter."""
    sql = """
    SELECT c.id, c.company_name, c.website,
    s.sector, s.industry
    FROM companies c
    LEFT JOIN sector_mapping s ON s.company_id = c.id
    """
    params = []
    if sector:
        sql += " WHERE s.sector = ?"
        params.append(sector)
    sql += " ORDER BY c.id"
    rows = db.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


@router.get("/company/{company_id}")
async def get_company_summary(
    company_id: int,
    snapshot_dir: SnapshotDir,
    _: CurrentUser,
    live: bool = Query(False, description="Use live analytics instead of snapshot"),
):
    """
    Full company summary.
    Default (live=false): reads from data/snapshots/company_summary.json.
    With ?live=true: calls compute_all_ratios + all summary functions in real time.
    """
    if not live:
        snap = Path(snapshot_dir) / "company_summary.json"
        if not snap.exists():
            raise HTTPException(503, "Snapshot not found; run export.py or use ?live=true")
        data = json.loads(snap.read_text())
        company = data.get(str(company_id))
        if company is None:
            raise HTTPException(404, f"company_id {company_id} not found in snapshot")
        return company

    from src.analytics.ratios import compute_all_ratios
    from src.analytics.pnl_trends import compute_sales_cagr, compute_profit_cagr
    from src.analytics.balance_health import compute_balance_health_summary
    from src.analytics.cashflow_quality import compute_cashflow_summary
    from src.analytics.price_analytics import compute_price_summary
    from src.analytics.sector_analytics import compute_peer_ranking

    return {
        "company_id": company_id,
        "latest_ratios": compute_all_ratios(company_id).tail(1).to_dict("records"),
        "sales_cagr_5yr": compute_sales_cagr(company_id, 5).get("sales_cagr"),
        "balance_health": compute_balance_health_summary(company_id),
        "cashflow": compute_cashflow_summary(company_id),
        "price": compute_price_summary(company_id),
        "peer_ranking": compute_peer_ranking(company_id, 2024),
    }


@router.get("/company/{company_id}/ratios", response_model=RatiosResponse)
async def get_company_ratios(
    company_id: int,
    _: CurrentUser,
    start_year: int | None = Query(None),
    end_year: int | None = Query(None),
):
    """ROE, ROCE, D/E, ICR per year. Optional year range filter."""
    from src.analytics.ratios import compute_all_ratios

    df = compute_all_ratios(company_id)
    if df.empty:
        raise HTTPException(404, f"No ratio data for company_id {company_id}")
    if start_year:
        df = df[df["year"] >= start_year]
    if end_year:
        df = df[df["year"] <= end_year]

    return RatiosResponse(
        company_id=company_id,
        ratios=[RatioYear(**row) for row in df.to_dict("records")],
    )


@router.get("/company/{company_id}/pnl", response_model=PnLResponse)
async def get_company_pnl(
    company_id: int,
    _: CurrentUser,
    cagr_years: int = Query(5, ge=1, le=10),
):
    """P&L trends: sales/profit CAGR, margin series, EPS unit flag count."""
    from src.analytics.pnl_trends import (
        compute_sales_cagr,
        compute_profit_cagr,
        compute_margin_series,
        compute_eps_trend,
    )

    margins = compute_margin_series(company_id)
    eps_df = compute_eps_trend(company_id)
    sc = compute_sales_cagr(company_id, cagr_years)
    pc = compute_profit_cagr(company_id, cagr_years)

    def _cagr_summary(d, val_key_start, val_key_end, cagr_key):
        if not d:
            return None
        return CAGRSummary(
            years=d["years"],
            start_year=d["start_year"],
            end_year=d["end_year"],
            start_value=d[val_key_start],
            end_value=d[val_key_end],
            cagr=d.get(cagr_key),
        )

    return PnLResponse(
        company_id=company_id,
        sales_cagr=_cagr_summary(sc, "start_sales", "end_sales", "sales_cagr"),
        profit_cagr=_cagr_summary(pc, "start_profit", "end_profit", "profit_cagr"),
        margin_series=[
            MarginYear(**r)
            for r in margins[["year", "operating_margin", "net_margin", "ebitda_margin"]].to_dict("records")
        ],
        eps_unit_flags=int(eps_df["eps_unit_flag"].sum()) if not eps_df.empty else 0,
    )
