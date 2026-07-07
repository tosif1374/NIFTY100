import streamlit as st
import pandas as pd
from api_client import get_companies, get_sectors
st.set_page_config(
page_title="Nifty 100 Financial Analytics",
page_icon="n",
layout="wide",
initial_sidebar_state="expanded",
)
st.title("n Nifty 100 Financial Analytics Dashboard")
st.caption("DecodeLabs × Bluestock Fintech | Sprint 4 Deliverable")
# Sidebar — sector filter
st.sidebar.header("Filters")
sectors_data = get_sectors()
sector_names = ["All Sectors"] + sorted({s["sector"] for s in sectors_data})
selected_sector = st.sidebar.selectbox("Sector", sector_names)
# Fetch companies (with optional sector filter)
companies = get_companies(
sector=None if selected_sector == "All Sectors" else selected_sector
)
df = pd.DataFrame(companies)
# Key metrics row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Companies Shown", len(df))
if "sector" in df.columns and selected_sector != "All Sectors":
    sector_row = next((s for s in sectors_data if s["sector"] == selected_sector), {})
col2.metric("Avg ROE", f"{sector_row.get('roe_mean','—')}%")
col3.metric("Avg ROCE", f"{sector_row.get('roce_mean','—')}%")
col4.metric("Avg D/E", f"{sector_row.get('de_mean','—')}")
# Company selector table
st.subheader("Select a Company")
st.dataframe(
df[["id","company_name","sector","industry"]].rename(columns={
"id": "ID", "company_name": "Company",
"sector": "Sector", "industry": "Industry"
}),
use_container_width=True,
hide_index=True,
)
st.info("Use the sidebar pages to deep-dive into a specific company, "
"compare sectors, or explore price analytics.")