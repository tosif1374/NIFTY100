import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = {
    "companies": [
        "id",
        "company_name",
        "website",
        "face_value",
        "book_value",
        "roe_percentage",
        "roce_percentage",
    ],
    "profitandloss": [
        "company_id",
        "year",
        "sales",
        "expenses",
        "operating_profit",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "net_profit",
        "eps",
        "dividend_payout",
    ],
    "balancesheet": [
        "company_id",
        "year",
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets",
    ],
    "cashflow": [
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ],
    "stock_prices": ["company_id", "date", "close_price", "volume"],
    "documents": ["company_id", "year", "annual_report_url"],
}


def load_csv_smart(filepath: str) -> pd.DataFrame:
    """Load a CSV file and normalize its column names to the expected schema."""
    path = Path(filepath)
    stem = path.stem.lower()

    df = pd.read_csv(path)
    expected = EXPECTED_COLUMNS.get(stem)

    if expected is None:
        logger.warning("No expected schema for '%s' — defaulting to CSV load", stem)
    else:
        matched = sum(1 for col in df.columns if str(col).strip().lower() in expected)
        logger.info(
            "Loaded %s with %d matching expected columns",
            path.name,
            matched,
        )

    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def load_all_core_files(raw_dir: str) -> dict[str, pd.DataFrame]:
    """Load all core CSV files into a dict keyed by file stem."""
    raw_path = Path(raw_dir)
    files = {
        "companies": raw_path / "companies.csv",
        "profitandloss": raw_path / "profitandloss.csv",
        "balancesheet": raw_path / "balancesheet.csv",
        "cashflow": raw_path / "cashflow.csv",
        "stock_prices": raw_path / "stock_prices.csv",
        "documents": raw_path / "documents.csv",
    }

    loaded = {}
    for name, path in files.items():
        if not path.exists():
            logger.error("Missing expected file: %s", path)
            continue
        loaded[name] = load_csv_smart(path)
    return loaded
