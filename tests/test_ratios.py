import sqlite3, pandas as pd
import pytest
import os
from unittest.mock import patch, MagicMock
from src.analytics.ratios import (compute_roe, compute_roce,
compute_debt_to_equity,
compute_interest_coverage,
compute_price_to_book,
compute_all_ratios)
# nn Fixtures 
@pytest.fixture(scope="module")
def seed_db(tmp_path_factory):
    """In-memory DB seeded with minimal data for 2 companies x 4 years."""
    db = tmp_path_factory.mktemp("data") / "test.db"
    conn = sqlite3.connect(str(db))
    conn.executescript(open("./db/schema.sql").read())
    conn.executemany("INSERT INTO companies VALUES (?,?,?,?,?,?,?)", [
    (1,"Reliance Industries","https://screener.in/company/RELIANCE/",10,668,8.91,10.3),
    (2,"TCS","https://screener.in/company/TCS/",1,296.61,45.59,54.93),
    ])
    # 4 years of P&L for company 1
    pnl = [(1,y,s,s*0.82,s*0.18,s*0.02,s*0.04,s*0.03,s*0.13,s*0.09,s*0.09/10,15.0)
    for y,s in [(2021,230000),(2022,260000),(2023,292000),(2024,320000)]]
    conn.executemany("INSERT INTO profit_and_loss VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", pnl)
    # Balance sheet
    bs = [(1,y,20000,ec*4,ec*2,ec*0.5,ec*7.5,ec*5,ec*0.5,ec*1,ec*1,ec*7.5)
    for y,ec in [(2021,28000),(2022,30000),(2023,32000),(2024,34000)]]
    conn.executemany("INSERT INTO balance_sheet VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", bs)
    # Cash flow
    cf = [(1,y,28000,-15000,-8000,5000) for y in [2021,2022,2023,2024]]
    conn.executemany("INSERT INTO cash_flow VALUES (?,?,?,?,?,?)", cf)
    # Monthly stock prices (Jan-Dec 2021-2024)
    import datetime
    rows = []
    price = 2000.0
    for yr in range(2021, 2025):
        for mo in range(1, 13):
            price *= 1.008
            rows.append((1, f"{yr}-{mo:02d}-01", round(price,2), 5000000))
    conn.executemany("INSERT INTO stock_prices VALUES (?,?,?,?)", rows)
    conn.commit()
    conn.close()
    
    return str(db)

# nn ROE tests 
def test_roe_returns_dataframe(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_roe(1)
    assert isinstance(df, pd.DataFrame)

def test_roe_has_expected_columns(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_roe(1)
    assert {"company_id","year","roe_pct"}.issubset(df.columns)

def test_roe_year_count(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_roe(1)
    assert len(df) == 4

def test_roe_values_positive(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_roe(1)
    assert (df["roe_pct"] > 0).all()

def test_roe_missing_company_returns_empty(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_roe(999)
    assert len(df) == 0
# nn ROCE tests 
def test_roce_returns_dataframe(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_roce(1)
    assert isinstance(df, pd.DataFrame)

def test_roce_has_expected_columns(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_roce(1)
    assert "roce_pct" in df.columns

def test_roce_values_reasonable(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_roce(1)
    assert (df["roce_pct"].between(-50, 200)).all()
# nn D/E tests 
def test_de_ratio_returns_dataframe(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_debt_to_equity(1)
    assert isinstance(df, pd.DataFrame)

def test_de_ratio_non_negative(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_debt_to_equity(1)
    assert (df["de_ratio"] >= 0).all()

# nn ICR tests 
def test_icr_returns_dataframe(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_interest_coverage(1)
    assert isinstance(df, pd.DataFrame)

def test_icr_formula_correct(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_interest_coverage(1).set_index("year")
    # ebit / interest should equal icr
    assert abs(df.loc[2021,"ebit"] / df.loc[2021,"interest"] - df.loc[2021,"icr"]) < 0.01
# nn P/B tests 
def test_pb_returns_dataframe(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_price_to_book(1)
    assert isinstance(df, pd.DataFrame)

def test_pb_positive_values(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_price_to_book(1)
    assert (df["pb_ratio"] > 0).all()

# nn compute_all_ratios nnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn
def test_all_ratios_columns(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_all_ratios(1)
    for col in ["roe_pct","roce_pct","de_ratio","icr"]:
        assert col in df.columns

def test_all_ratios_sorted_by_year(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_all_ratios(1)
    assert list(df["year"]) == sorted(df["year"])

def test_all_ratios_row_count(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_all_ratios(1)
    assert len(df) == 4

def test_all_ratios_no_duplicate_years(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_all_ratios(1)
    assert df["year"].nunique() == len(df)

def test_missing_company_all_ratios_empty(seed_db, mock_db_for_test):
    with patch("src.analytics.db.get_connection", mock_db_for_test(seed_db)):
        df = compute_all_ratios(999)
    assert len(df) == 0
