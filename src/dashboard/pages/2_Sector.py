import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from api_client import get_sectors, get_sector_detail, get_peers
st.set_page_config(page_title="Sector Comparison", layout="wide")
st.title("n Sector Comparison")
year = st.sidebar.slider("Fiscal Year", 2020, 2024, 2024)
sectors = get_sectors(year=year)
df_sectors = pd.DataFrame(sectors).dropna(subset=["roe_mean","roce_mean"])
# nn Bubble chart: ROE vs ROCE, sized by n_companies 
st.subheader("All Sectors — ROE vs ROCE")
fig = px.scatter(
df_sectors,
x="roce_mean", y="roe_mean",
size="n_companies", color="sector",
text="sector", size_max=40,
labels={"roce_mean":"Mean ROCE %","roe_mean":"Mean ROE %"},
title=f"Sector Bubble Chart (FY{year})",
height=500,
)
fig.update_traces(textposition="top center")
fig.add_hline(y=15, line_dash="dash", line_color="gray",
annotation_text="15% ROE benchmark")
st.plotly_chart(fig, use_container_width=True)
# nn Sector detail table 
st.subheader("Sector Averages")
st.dataframe(
df_sectors[[
"sector","n_companies","roe_mean","roe_median","roce_mean","de_mean","op_margin_mean"
]].rename(columns={
"sector":"Sector","n_companies":"Companies",
"roe_mean":"ROE% (avg)","roe_median":"ROE% (med)",
"roce_mean":"ROCE% (avg)","de_mean":"D/E (avg)","op_margin_mean":"Op Margin% (avg)"
}).sort_values("ROE% (avg)", ascending=False),
use_container_width=True, hide_index=True,
)
# nn Peer ranking for a selected company 
st.subheader("Peer Ranking")
from api_client import get_companies
companies = get_companies()
company_map = {c["company_name"]: c["id"] for c in companies}

selected = st.selectbox("Select Company for Peer Ranking", sorted(company_map.keys()))
peers = get_peers(company_map[selected], year=year)
if "error" not in peers:
    c1,c2,c3 = st.columns(3)
c1.metric("Sector", peers.get("sector","—"))
c2.metric("ROE Rank", f"{peers.get('roe_rank','—')} / {peers.get('n_peers','—')}")
c3.metric("ROE Percentile", f"{peers.get('roe_percentile','—')}%")
detail = get_sector_detail(peers["sector"], year=year)
if "companies" in detail:
    st.dataframe(pd.DataFrame(detail["companies"])
.sort_values("roe_pct", ascending=False),
use_container_width=True, hide_index=True)