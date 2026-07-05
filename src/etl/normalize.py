import re
import pandas as pd


def normalize_year(raw_value) -> int | None:
    """
    Normalize a messy fiscal-year value to a canonical 4-digit int
    representing the FY-end calendar year (Indian convention: FY24 -> 2024).
    Handles:
    - "FY24", "FY 2024", "FY2024" -> 2024
    - "2023-24", "2023-2024" -> 2024 (FY-end year)
    - "Mar-24", "Mar-2024", "March 24" -> 2024
    - 2024, 2024.0, "2024" -> 2024
    - None / NaN / unparsable -> None
    """
    if raw_value is None or (isinstance(raw_value, float) and pd.isna(raw_value)):
        return None

    # Already a clean int/float year
    if isinstance(raw_value, (int, float)) and not isinstance(raw_value, bool):
        year = int(raw_value)
        if 1990 <= year <= 2100:
            return year
        return None

    text = str(raw_value).strip()
    if not text or text.lower() in {"nan", "none", "n/a", "-"}:
        return None

    # "2023-24" or "2023-2024" -> take the second (FY-end) year
    m = re.match(r"^(\d{4})\s*-\s*(\d{2,4})$", text)
    if m:
        start, end = m.group(1), m.group(2)
        if len(end) == 2:
            end_year = int(start[:2] + end)
        else:
            end_year = int(end)
        return end_year

    # "FY24", "FY 2024", "FY2024"
    m = re.match(r"^FY\s*(\d{2,4})$", text, re.IGNORECASE)
    if m:
        digits = m.group(1)
        return int("20" + digits) if len(digits) == 2 else int(digits)

    # "Mar-24", "Mar 2024", "March-24"
    m = re.match(r"^[A-Za-z]{3,9}[\s\-]?(\d{2,4})$", text)
    if m:
        digits = m.group(1)
        return int("20" + digits) if len(digits) == 2 else int(digits)

    # Plain 4-digit year as string
    m = re.match(r"^(\d{4})(\.0)?$", text)
    if m:
        return int(m.group(1))

    return None  # unparsable — caller should log and route to validation_failures.csv


def normalize_ticker(raw_value: str, known_symbols: set[str] | None = None) -> str | None:
    """
    Normalize a raw ticker/symbol string to the bare NSE symbol.
    Handles:
    - "TCS.NS", "tcs.ns" -> "TCS"
    - "TCS.BO", "RELIANCE.BSE" -> "TCS", "RELIANCE"
    - " Infy " -> "INFY"
    - "BAJAJ-AUTO" -> "BAJAJ-AUTO" (hyphens preserved — valid in real symbols)
    - "" / None / NaN -> None
    - unrecognized symbol not in known_symbols -> None (logged for review)
    """
    if raw_value is None or (isinstance(raw_value, float) and pd.isna(raw_value)):
        return None

    text = str(raw_value).strip().upper()
    if not text:
        return None

    # Strip common exchange suffixes
    for suffix in (".NS", ".BO", ".BSE", ".NSE"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break

    text = text.strip()
    if known_symbols is not None and text not in known_symbols:
        return None  # caller logs to validation_failures.csv with reason "unknown_ticker"

    return text