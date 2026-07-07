
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
# Company 
class CompanyBase(BaseModel):
    id: int
    company_name: str
    website: Optional[str] = None
class CompanyList(CompanyBase):
    sector: Optional[str] = None
    industry: Optional[str] = None
class RatioYear(BaseModel):
    year: int
    roe_pct: Optional[float] = None
    roce_pct: Optional[float] = None
    de_ratio: Optional[float] = None
    icr: Optional[float] = None
class RatiosResponse(BaseModel):
    company_id: int
    ratios: list[RatioYear]
# P&L Trends 
class CAGRSummary(BaseModel):
    years: int
    start_year: int
    end_year: int
    start_value: float
    end_value: float
    cagr: Optional[float] = None
class MarginYear(BaseModel):
    year: int
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    ebitda_margin: Optional[float] = None
class PnLResponse(BaseModel):
    company_id: int
    sales_cagr: Optional[CAGRSummary] = None
    profit_cagr: Optional[CAGRSummary] = None
    margin_series: list[MarginYear]
    eps_unit_flags: int = Field(0, description="Count of years with EPS unit mismatch flag")
# Balance Sheet 
class BalanceHealthResponse(BaseModel):
    company_id: int
    latest_year: Optional[int] = None
    de_ratio: Optional[float] = None
    de_trend_3yr: Optional[float] = None
    current_ratio: Optional[float] = None
    fixed_asset_ratio: Optional[float] = None
    cwip_ratio: Optional[float] = None
    asset_growth_yoy: Optional[float] = None

# Cash Flow 
class CashFlowResponse(BaseModel):
    company_id: int
    latest_year: Optional[int] = None
    latest_fcf: Optional[float] = None
    fcf_3yr_avg: Optional[float] = None
    latest_cfo: Optional[float] = None
    latest_cfo_np_ratio: Optional[float] = None
    cfo_quality_flag: Optional[str] = None
# Price 
class PriceResponse(BaseModel):
    company_id: int
    latest_price: Optional[float] = None
    latest_date: Optional[str] = None
    return_12m_pct: Optional[float] = None
    annualised_return_pct: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    latest_rolling_sharpe: Optional[float] = None
#  Peers 
class PeerRankingResponse(BaseModel):
    company_id: int
    sector: Optional[str] = None
    year: Optional[int] = None
    n_peers: Optional[int] = None
    roe_pct: Optional[float] = None
    roe_rank: Optional[int] = None
    roe_percentile: Optional[float] = None
    roce_pct: Optional[float] = None
    op_margin_pct: Optional[float] = None
#  Sectors 
class SectorSummary(BaseModel):
    sector: str
    year: int
    n_companies: int
    roe_mean: Optional[float] = None
    roe_median: Optional[float] = None
    roce_mean: Optional[float] = None
    de_mean: Optional[float] = None
    op_margin_mean: Optional[float] = None
class SectorDetail(BaseModel):
    sector: str
    year: int
    companies: list[dict] # company-level rows from compute_sector_averages()

# nn Auth
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
class TokenData(BaseModel):
    username: Optional[str] = None