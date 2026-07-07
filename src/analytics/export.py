
"""
Generates snapshot files consumed by the Sprint 3 API.
Run: python -m src.analytics.export
Outputs to: data/snapshots/
"""
import json
import pandas as pd
from pathlib import Path
from .db import query_df
from .ratios import compute_all_ratios
from .pnl_trends import compute_sales_cagr, compute_profit_cagr, compute_margin_series
from .balance_health import compute_balance_health_summary
from .cashflow_quality import compute_cashflow_summary
from .price_analytics import compute_price_summary
from .sector_analytics import compute_all_sectors_latest, compute_peer_ranking
SNAPSHOT_DIR = Path("./data/snapshots")
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
from .db import query_df

LATEST_YEAR = int(
    query_df(
        "SELECT MAX(year) AS latest_year FROM profit_and_loss"
    ).iloc[0]["latest_year"]
)
def _load_company_ids() -> list[int]:
    df = query_df("SELECT id FROM companies ORDER BY id")
    return list(df["id"].astype(int))
def export_ratios_csv():
    """One row per (company_id, year) with all 4 key ratios."""
    ids = _load_company_ids()
    frames = []
    for cid in ids:
        df = compute_all_ratios(cid)
        if not df.empty:
            frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(SNAPSHOT_DIR / "ratios_all.csv", index=False)
    print(f"ratios_all.csv: {len(out)} rows")
def export_company_summary_json():
    """
    One JSON object per company containing:
    - latest ratios, P&L CAGRs, balance health, cash flow quality, price summary.
    Saved as data/snapshots/company_summary.json
    This is the primary payload for Sprint 3's GET /api/company/{id} endpoint.
    """
    ids = _load_company_ids()
    meta = query_df("SELECT id, company_name, website FROM companies")
    meta_map = {int(r["id"]): r for _, r in meta.iterrows()}
    summaries = {}
    for cid in ids:
        try:
            ratios_df = compute_all_ratios(cid)
            latest_ratios = {}
            if not ratios_df.empty:
                lr = ratios_df.iloc[-1]
                latest_ratios = {
                    "year": int(lr["year"]),
                    "roe_pct": lr["roe_pct"],
                    "roce_pct": lr["roce_pct"],
                    "de_ratio": lr["de_ratio"],
                    "icr": lr["icr"],
                }
            summaries[cid] = {
                "company_id": cid,
                "company_name": meta_map[cid]["company_name"] if cid in meta_map else None,
                "website": meta_map[cid]["website"] if cid in meta_map else None,
                "latest_ratios": latest_ratios,
                "sales_cagr_5yr": compute_sales_cagr(cid, 5).get("sales_cagr"),
                "profit_cagr_5yr": compute_profit_cagr(cid, 5).get("profit_cagr"),
                "balance_health": compute_balance_health_summary(cid),
                "cashflow": compute_cashflow_summary(cid),
                "price": compute_price_summary(cid),
                "peer_ranking": compute_peer_ranking(cid, LATEST_YEAR),
            }
        except Exception as e:
            summaries[cid] = {"company_id": cid, "error": str(e)}
    with open(SNAPSHOT_DIR / "company_summary.json", "w") as f:
        json.dump(summaries, f, indent=2, default=str)
    print(f"company_summary.json: {len(summaries)} companies")
def export_sector_comparison_csv():
    """Cross-sector comparison table for the latest year."""
    df = compute_all_sectors_latest(LATEST_YEAR)
    df.to_csv(SNAPSHOT_DIR / "sector_comparison.csv", index=False)
    print(f"sector_comparison.csv: {len(df)} sectors")
def run_all_exports():
    print("Starting Sprint 2 export run...")
    export_ratios_csv()
    export_company_summary_json()
    export_sector_comparison_csv()
    print("All snapshots written to", SNAPSHOT_DIR)

if __name__ == "__main__":
    run_all_exports()
