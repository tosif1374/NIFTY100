
# src/dashboard/pages/1_Company.py
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from api_client import (get_companies, get_ratios, get_pnl,
get_balance, get_cashflow, get_peers)
from components.chart import (ratio_trend_chart, margin_trend_chart,
cashflow_quality_chart, balance_bar_chart)
st.set_page_config(page_title="Company Deep-Dive", layout="wide")
st.title("n Company Deep-Dive")
# Company selector
companies = get_companies()

company_map = {c["company_name"]: c["id"] for c in companies}
selected_name = st.selectbox("Select Company", sorted(company_map.keys()))
company_id = company_map[selected_name]
# nn Key metrics header
ratios_data = get_ratios(company_id)
ratios = ratios_data.get("ratios", [])
if ratios:
    latest = ratios[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("ROE %", f"{latest.get('roe_pct','—')}%",
help="Return on Equity — latest year")
c2.metric("ROCE %", f"{latest.get('roce_pct','—')}%",
help="Return on Capital Employed — latest year")
c3.metric("D/E Ratio",f"{latest.get('de_ratio','—')}",
help="Debt-to-Equity — latest year")
c4.metric("ICR", f"{latest.get('icr','—')}x",
help="Interest Coverage Ratio — latest year")
# nn Ratio trend chart 
st.plotly_chart(ratio_trend_chart(ratios, f"{selected_name} — Ratio Trends"),
use_container_width=True)
# nn P&L trends 
st.subheader("Profit & Loss Trends")
pnl = get_pnl(company_id)
col1, col2 = st.columns(2)
if pnl.get("sales_cagr"):
    sc = pnl["sales_cagr"]
col1.metric("Sales CAGR (5yr)",
f"{sc['cagr']*100:.1f}%" if sc.get('cagr') else "—",
help=f"FY{sc['start_year']} ® FY{sc['end_year']}")
if pnl.get("profit_cagr"):
    pc = pnl["profit_cagr"]
col2.metric("Profit CAGR (5yr)",
f"{pc['cagr']*100:.1f}%" if pc.get('cagr') else "—")
if pnl.get("margin_series"):
    st.plotly_chart(margin_trend_chart(pnl["margin_series"]),
use_container_width=True)
if pnl.get("eps_unit_flags", 0) > 0:
    st.warning(f"n {pnl['eps_unit_flags']} year(s) flagged for EPS unit inconsistency.")
# nn Balance sheet health 
st.subheader("Balance Sheet Health")
balance = get_balance(company_id)
if "error" not in balance:
    trend = balance.get("de_trend_3yr")
if trend is not None:
    delta_label = f"3yr D: {'s' if trend > 0 else 't'} {abs(trend):.2f}"
st.caption(f"D/E Trend: {delta_label} ({'rising leverage n' if trend > 0.2 else 'stable'})")
st.plotly_chart(balance_bar_chart(balance), use_container_width=True)
# nn Cash flow quality 
st.subheader("Cash Flow Quality")
cf = get_cashflow(company_id)
if "error" not in cf:
    col1, col2 = st.columns([1, 2])
with col1:
    st.plotly_chart(cashflow_quality_chart(cf), use_container_width=True)
with col2:
    flag = cf.get("cfo_quality_flag","—")
colours = {"excellent":"n","acceptable":"n","warning":"n","red_flag":"n"}
st.markdown(f"**Quality Flag:** {colours.get(flag,'')} {flag.upper()}")
st.metric("Latest FCF (n Cr)", f"{cf.get('latest_fcf','—'):,.0f}")
st.metric("3-Year Avg FCF (n Cr)", f"{cf.get('fcf_3yr_avg','—'):,.0f}")
# nn Peer ranking 
st.subheader("Peer Ranking (Sector)")

peers = get_peers(company_id)
if "error" not in peers:
    st.caption(f"Sector: {peers.get('sector','—')} | "
f"ROE Rank: {peers.get('roe_rank','—')} / {peers.get('n_peers','—')} | "
f"ROE Percentile: {peers.get('roe_percentile','—')}%")