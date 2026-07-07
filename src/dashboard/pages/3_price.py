import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from api_client import get_companies, get_price
st.set_page_config(page_title="Price Analytics", layout="wide")
st.title("n Price Analytics")
companies = get_companies()
company_map = {c["company_name"]: c["id"] for c in companies}
selected = st.selectbox("Select Company", sorted(company_map.keys()))
cid = company_map[selected]
price_data = get_price(cid)
if "error" in price_data:
    st.warning(f"No price data: {price_data['error']}")
st.stop()
# nn Key metrics 
c1,c2,c3,c4 = st.columns(4)
c1.metric("Latest Price", f"n{price_data.get('latest_price','—'):,.2f}")
c2.metric("12M Return", f"{price_data.get('return_12m_pct','—')}%")
c3.metric("Max Drawdown", f"{price_data.get('max_drawdown_pct','—')}%")
c4.metric("Rolling Sharpe (12M)", f"{price_data.get('latest_rolling_sharpe','—'):.2f}"
if price_data.get('latest_rolling_sharpe') else "—")
# nn Monthly returns from raw data (need to call live mode) 
import requests, os
API_BASE = os.getenv("API_BASE_URL","http://localhost:8000")
st.subheader("Price Summary")
st.info(
f"Annualised Return: **{price_data.get('annualised_return_pct','—')}%** | "
f"Period: {price_data.get('latest_date','—')} (latest)"
)
st.caption(
"For full monthly price charts and rolling Sharpe time series, "
"the dashboard would call the live analytics endpoint (/price?live=true) "
"returning the full time series. The summary above comes from the snapshot."
)
# nn Sharpe ratio colour indicator 
sharpe = price_data.get("latest_rolling_sharpe")
if sharpe is not None:
    if sharpe >= 2: quality, colour = "Excellent", "n"
elif sharpe >= 1: quality, colour = "Good", "n"
elif sharpe >= 0: quality, colour = "Moderate", "n"
else: quality, colour = "Negative", "n"
st.markdown(f"**Risk-Adjusted Return Quality:** {colour} {quality} "
f"(Sharpe = {sharpe:.2f})")