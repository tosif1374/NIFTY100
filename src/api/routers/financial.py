from fastapi import APIRouter, HTTPException

from ..deps import CurrentUser
from ..schemas import BalanceHealthResponse, CashFlowResponse, PriceResponse

router = APIRouter()


@router.get("/company/{company_id}/balance", response_model=BalanceHealthResponse)
async def get_balance_health(company_id: int, _: CurrentUser):
    """
    Balance sheet health summary for latest available year.
    Includes: D/E ratio, 3-year D/E trend, current ratio proxy,
    fixed-asset ratio, CWIP ratio, YoY asset growth.
    """
    from src.analytics.balance_health import compute_balance_health_summary

    result = compute_balance_health_summary(company_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return BalanceHealthResponse(**result)


@router.get("/company/{company_id}/cashflow", response_model=CashFlowResponse)
async def get_cashflow_quality(company_id: int, _: CurrentUser):
    """
    Cash flow quality summary.
    Includes: latest FCF, 3-year FCF average, CFO, CFO/NP ratio,
    and quality flag (excellent / acceptable / warning / red_flag).
    """
    from src.analytics.cashflow_quality import compute_cashflow_summary

    result = compute_cashflow_summary(company_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return CashFlowResponse(**result)


@router.get("/company/{company_id}/price", response_model=PriceResponse)
async def get_price_analytics(company_id: int, _: CurrentUser):
    """
    Stock price analytics from monthly 2020-2024 data.
    Includes: latest price, 12-month return, annualised return,
    maximum drawdown, latest 12-month rolling Sharpe ratio.
    Returns 404 if company has no price data loaded.
    """
    from src.analytics.price_analytics import compute_price_summary

    result = compute_price_summary(company_id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return PriceResponse(**result)


@router.get("/company/{company_id}/peers")
async def get_peer_ranking(
    company_id: int,
    _: CurrentUser,
    year: int = 2024,
):
    """
    Peer ranking within sector for a given fiscal year.
    Returns: sector name, total peers, ROE rank, ROE percentile,
    ROCE, and operating margin vs sector.
    """
    from src.analytics.sector_analytics import compute_peer_ranking

    result = compute_peer_ranking(company_id, year)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result