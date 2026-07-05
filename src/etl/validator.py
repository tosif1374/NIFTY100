import re
import pandas as pd
from dataclasses import dataclass, field


@dataclass
class ValidationFailure:
    file: str
    rule_id: str
    row_index: int
    company_id: object
    year: object
    message: str


@dataclass
class ValidationReport:
    failures: list[ValidationFailure] = field(default_factory=list)

    def add(self, file, rule_id, row_index, company_id, year, message):
        self.failures.append(
            ValidationFailure(file, rule_id, row_index, company_id, year, message)
        )

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame([f.__dict__ for f in self.failures])

    def save_csv(self, path):
        self.to_dataframe().to_csv(path, index=False)


def validate_company_id(df, file_name, valid_company_ids, report: ValidationReport):
    # DQ-01: not null
    null_mask = df["company_id"].isna()
    for idx in df[null_mask].index:
        report.add(
            file_name,
            "DQ-01",
            idx,
            None,
            df.at[idx, "year"] if "year" in df else None,
            "company_id is null",
        )

    # DQ-02: must exist in companies.id
    bad_fk = ~df["company_id"].isin(valid_company_ids) & ~null_mask
    for idx in df[bad_fk].index:
        report.add(
            file_name,
            "DQ-02",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"] if "year" in df else None,
            f"company_id={df.at[idx, 'company_id']} not found in companies.id",
        )


def validate_year(df, file_name, report: ValidationReport, current_year=2026):
    from .normalize import normalize_year

    normalized = df["year"].apply(normalize_year)

    # DQ-03: must parse
    unparsable = normalized.isna() & df["year"].notna()
    for idx in df[unparsable].index:
        report.add(
            file_name,
            "DQ-03",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"],
            f"year value '{df.at[idx, 'year']}' did not normalize",
        )

    # DQ-04: range check
    out_of_range = normalized.notna() & ((normalized < 2000) | (normalized > current_year))
    for idx in df[out_of_range].index:
        report.add(
            file_name,
            "DQ-04",
            idx,
            df.at[idx, "company_id"],
            normalized.at[idx],
            f"year {normalized.at[idx]} outside [2000, {current_year}]",
        )
    return normalized


def validate_duplicates(df, file_name, report: ValidationReport):
    # DQ-05: unique (company_id, year)
    dupes = df.duplicated(subset=["company_id", "year"], keep=False)
    for idx in df[dupes].index:
        report.add(
            file_name,
            "DQ-05",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"],
            "duplicate (company_id, year) pair",
        )


def validate_profitandloss(df, report: ValidationReport):
    # DQ-06: sales >= 0
    bad = df["sales"] < 0
    for idx in df[bad].index:
        report.add(
            "profitandloss",
            "DQ-06",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"],
            f"sales={df.at[idx, 'sales']} is negative",
        )

    # DQ-07: net_profit reasonableness
    bad = df["net_profit"].abs() > (df["sales"].abs() * 5)
    for idx in df[bad].index:
        report.add(
            "profitandloss",
            "DQ-07",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"],
            "net_profit magnitude implausible relative to sales",
        )

    # DQ-08: eps numeric
    def not_numeric(v):
        try:
            float(v)
            return False
        except (TypeError, ValueError):
            return pd.notna(v)

    bad = df["eps"].apply(not_numeric)
    for idx in df[bad].index:
        report.add(
            "profitandloss",
            "DQ-08",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"],
            f"eps='{df.at[idx, 'eps']}' is not numeric",
        )


def validate_balancesheet(df, report: ValidationReport, tolerance=0.01):
    computed_assets = df["fixed_assets"] + df["cwip"] + df["investments"] + df["other_asset"]
    bad = (computed_assets - df["total_assets"]).abs() > (df["total_assets"].abs() * tolerance)
    for idx in df[bad].index:
        report.add(
            "balancesheet",
            "DQ-09",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"],
            "fixed_assets+cwip+investments+other_asset != total_assets (>1%)",
        )

    computed_liab = (
        df["equity_capital"]
        + df["reserves"]
        + df["borrowings"]
        + df["other_liabilities"]
    )
    bad = (computed_liab - df["total_liabilities"]).abs() > (df["total_liabilities"].abs() * tolerance)
    for idx in df[bad].index:
        report.add(
            "balancesheet",
            "DQ-10",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"],
            "equity+reserves+borrowings+other_liab != total_liabilities (>1%)",
        )

    bad = (df["total_assets"] - df["total_liabilities"]).abs() > (df["total_assets"].abs() * tolerance)
    for idx in df[bad].index:
        report.add(
            "balancesheet",
            "DQ-11",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"],
            "total_assets does not balance against total_liabilities (>1%)",
        )


def validate_cashflow(df, report: ValidationReport, tolerance=0.01):
    computed = df["operating_activity"] + df["investing_activity"] + df["financing_activity"]
    bad = (computed - df["net_cash_flow"]).abs() > (df["net_cash_flow"].abs() * tolerance + 0.01)
    for idx in df[bad].index:
        report.add(
            "cashflow",
            "DQ-12",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"],
            "operating+investing+financing != net_cash_flow (>1%)",
        )


def validate_stock_prices(df, report: ValidationReport):
    bad = df["close_price"] <= 0
    for idx in df[bad].index:
        report.add(
            "stock_prices",
            "DQ-13",
            idx,
            df.at[idx, "company_id"],
            None,
            f"close_price={df.at[idx, 'close_price']} <= 0",
        )

    bad = df["volume"] < 0
    for idx in df[bad].index:
        report.add(
            "stock_prices",
            "DQ-14",
            idx,
            df.at[idx, "company_id"],
            None,
            f"volume={df.at[idx, 'volume']} < 0",
        )

    parsed = pd.to_datetime(df["date"], errors="coerce")
    bad = parsed.isna() | (parsed.dt.year < 2020) | (parsed.dt.year > 2024)
    for idx in df[bad].index:
        report.add(
            "stock_prices",
            "DQ-15",
            idx,
            df.at[idx, "company_id"],
            None,
            f"date='{df.at[idx, 'date']}' invalid or outside 2020-2024",
        )


URL_RE = re.compile(r"^https?://[^\s]+\.[^\s]{2,}$")


def validate_documents(df, report: ValidationReport):
    bad = df["annual_report_url"].notna() & ~df["annual_report_url"].astype(str).str.match(URL_RE)
    for idx in df[bad].index:
        url_val = df.at[idx, "annual_report_url"]
        report.add(
            "documents",
            "DQ-16",
            idx,
            df.at[idx, "company_id"],
            df.at[idx, "year"],
            f"annual_report_url='{url_val}' malformed",
        )
