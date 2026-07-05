import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path

from ..deps import CurrentUser, SnapshotDir
from ..schemas import SectorSummary

router = APIRouter()


@router.get("/sectors", response_model=list[SectorSummary])
async def list_sectors(
    snapshot_dir: SnapshotDir,
    _: CurrentUser,
    year: int = Query(2024, ge=2000, le=2030),
):
    """
    Cross-sector comparison table from pre-computed snapshot.
    Returns mean ROE, ROCE, D/E, and operating margin per sector
    for the specified fiscal year (default: 2024).
    """
    snap = Path(snapshot_dir) / "sector_comparison.csv"
    if not snap.exists():
        raise HTTPException(503, "Sector snapshot not found; run export.py first")

    df = pd.read_csv(snap)
    if "year" in df.columns:
        df = df[df["year"] == year]
    if df.empty:
        raise HTTPException(404, f"No sector data for year {year}")
    return df.to_dict("records")


@router.get("/sectors/{sector_name}")
async def get_sector_detail(
    sector_name: str,
    _: CurrentUser,
    year: int = Query(2024, ge=2000, le=2030),
):
    """
    Detailed breakdown for a single sector: all companies with their
    ROE, ROCE, D/E, operating margin, and net margin for the given year.
    Companies sorted by ROE descending.
    """
    from src.analytics.sector_analytics import compute_sector_averages

    df = compute_sector_averages(sector_name, year)
    if df.empty:
        raise HTTPException(404, f"No data for sector '{sector_name}' in year {year}")
    return {
        "sector": sector_name,
        "year": year,
        "companies": df.to_dict("records"),
    }


@router.get("/sector-names", response_model=list[str])
async def list_sector_names(db: "DbDep", _: CurrentUser):
    """Utility: list all distinct sector names from sector_mapping."""
    from ..deps import DbDep

    rows = db.execute(
        "SELECT DISTINCT sector FROM sector_mapping ORDER BY sector"
    ).fetchall()
    return [r["sector"] for r in rows]