from .excel_loader import load_all_core_files
from .validator import (
    ValidationReport,
    validate_company_id,
    validate_year,
    validate_duplicates,
    validate_profitandloss,
    validate_balancesheet,
    validate_cashflow,
    validate_stock_prices,
    validate_documents,
)


def run_all_validations(raw_dir: str, out_path: str):
    data = load_all_core_files(raw_dir)
    report = ValidationReport()
    valid_ids = set(data["companies"]["id"])

    for name in ["profitandloss", "balancesheet", "cashflow", "stock_prices", "documents"]:
        df = data[name]
        validate_company_id(df, name, valid_ids, report)
        if "year" in df.columns:
            validate_year(df, name, report)
        validate_duplicates(df, name, report)

    validate_profitandloss(data["profitandloss"], report)
    validate_balancesheet(data["balancesheet"], report)
    validate_cashflow(data["cashflow"], report)
    validate_stock_prices(data["stock_prices"], report)
    validate_documents(data["documents"], report)

    report.save_csv(out_path)
    print(f"Validation complete: {len(report.failures)} failures logged to {out_path}")
    return report


if __name__ == "__main__":
    run_all_validations("./data/raw", "./data/validation/validation_failures.csv")