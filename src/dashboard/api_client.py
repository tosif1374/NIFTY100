import os
import requests
import streamlit as st
from functools import wraps

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
API_USER = os.getenv("API_USERNAME", "analyst")
API_PASS = os.getenv("API_PASSWORD", "nifty100pass")


def _get_token() -> str:
    """
    Fetch and cache JWT token in Streamlit session state.
    Re-fetches automatically if session resets or token expires.
    """
    if "api_token" not in st.session_state:
        r = requests.post(
            f"{API_BASE}/auth/token",
            data={"username": API_USER, "password": API_PASS},
            timeout=10,
        )
        r.raise_for_status()
        st.session_state["api_token"] = r.json()["access_token"]

    return st.session_state["api_token"]


def _get(endpoint: str, params: dict = None) -> dict | list:
    """Authenticated GET with automatic token injection."""
    token = _get_token()

    r = requests.get(
        f"{API_BASE}{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {},
        timeout=15,
    )

    if r.status_code == 401:
        # Token expired — clear cache and retry once
        del st.session_state["api_token"]

        token = _get_token()
        r = requests.get(
            f"{API_BASE}{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            params=params or {},
            timeout=15,
        )

    r.raise_for_status()
    return r.json()


# Typed API functions — one per endpoint

@st.cache_data(ttl=300)
def get_companies(sector: str = None) -> list[dict]:
    params = {"sector": sector} if sector else {}
    return _get("/api/v1/companies", params)


@st.cache_data(ttl=300)
def get_company_summary(company_id: int) -> dict:
    return _get(f"/api/v1/company/{company_id}")


@st.cache_data(ttl=300)
def get_ratios(
    company_id: int,
    start_year: int = None,
    end_year: int = None,
) -> dict:
    params = {}

    if start_year:
        params["start_year"] = start_year

    if end_year:
        params["end_year"] = end_year

    return _get(f"/api/v1/company/{company_id}/ratios", params)


@st.cache_data(ttl=300)
def get_pnl(company_id: int) -> dict:
    return _get(f"/api/v1/company/{company_id}/pnl")


@st.cache_data(ttl=300)
def get_balance(company_id: int) -> dict:
    return _get(f"/api/v1/company/{company_id}/balance")


@st.cache_data(ttl=300)
def get_cashflow(company_id: int) -> dict:
    return _get(f"/api/v1/company/{company_id}/cashflow")


@st.cache_data(ttl=300)
def get_price(company_id: int) -> dict:
    return _get(f"/api/v1/company/{company_id}/price")


@st.cache_data(ttl=300)
def get_peers(company_id: int, year: int = 2024) -> dict:
    return _get(f"/api/v1/company/{company_id}/peers", {"year": year})


@st.cache_data(ttl=600)
def get_sectors(year: int = 2024) -> list[dict]:
    return _get("/api/v1/sectors", {"year": year})


@st.cache_data(ttl=300)
def get_sector_detail(sector_name: str, year: int = 2024) -> dict:
    return _get(f"/api/v1/sectors/{sector_name}", {"year": year})