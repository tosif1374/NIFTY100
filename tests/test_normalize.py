import pytest
from src.etl.normalize import normalize_year, normalize_ticker


# --- normalize_year(): 20 cases -------------------------------------------
YEAR_CASES = [
    ("FY24", 2024),
    ("FY 2024", 2024),
    ("FY2024", 2024),
    ("fy24", 2024),
    ("2023-24", 2024),
    ("2023-2024", 2024),
    ("Mar-24", 2024),
    ("March 2024", 2024),
    ("Mar2024", 2024),
    (2024, 2024),
    (2024.0, 2024),
    ("2024", 2024),
    ("2024.0", 2024),
    ("2012-03-01", 2012),
    ("2023-09-01", 2023),
    (None, None),
    (float("nan"), None),
    ("", None),
    ("N/A", None),
    ("garbage", None),
    (1989, None),
    (2101, None),
]


@pytest.mark.parametrize("raw,expected", YEAR_CASES)
def test_normalize_year(raw, expected):
    assert normalize_year(raw) == expected


# --- normalize_ticker(): 20 cases ------------------------------------------
KNOWN = {"TCS", "INFY", "RELIANCE", "BAJAJ-AUTO", "M&M"}
TICKER_CASES = [
    ("TCS.NS", "TCS"),
    ("tcs.ns", "TCS"),
    ("TCS.BO", "TCS"),
    (" Infy ", "INFY"),
    ("infy.ns", "INFY"),
    ("RELIANCE.BSE", "RELIANCE"),
    ("RELIANCE.NSE", "RELIANCE"),
    ("BAJAJ-AUTO", "BAJAJ-AUTO"),
    ("bajaj-auto.ns", "BAJAJ-AUTO"),
    ("M&M", "M&M"),
    ("m&m.ns", "M&M"),
    ("", None),
    (None, None),
    (float("nan"), None),
    ("UNKNOWNTICKER", None),
    ("123XYZ", None),
    ("TCS ", "TCS"),
    (" .NS", None),
    ("Tcs.Ns", "TCS"),
    ("tcs", "TCS"),
]


@pytest.mark.parametrize("raw,expected", TICKER_CASES)
def test_normalize_ticker(raw, expected):
    assert normalize_ticker(raw, known_symbols=KNOWN) == expected