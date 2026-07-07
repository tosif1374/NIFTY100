# src/dashboard/components/charts.py
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
NAVY = "#1F4E78"
BLUE = "#2563eb"
GREEN = "#15803d"
ORANGE = "#ea580c"
RED = "#dc2626"
def ratio_trend_chart(ratios: list[dict], title: str = "Financial Ratios Over Time"):
    """
Multi-line chart: ROE %, ROCE % on primary axis; D/E ratio on secondary axis.
"""
    df = pd.DataFrame(ratios)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["year"], y=df["roe_pct"],
    name="ROE %", line=dict(color=BLUE, width=2.5)))
    fig.add_trace(go.Scatter(x=df["year"], y=df["roce_pct"],
    name="ROCE %", line=dict(color=GREEN, width=2.5)))
    fig.add_trace(go.Scatter(x=df["year"], y=df["de_ratio"],
    name="D/E Ratio", line=dict(color=ORANGE, width=2,
    dash="dot"), yaxis="y2"))
    fig.update_layout(
    title=title,
    xaxis_title="Fiscal Year",
    yaxis=dict(title="Return %", ticksuffix="%"),
    yaxis2=dict(title="D/E Ratio", overlaying="y", side="right"),
    legend=dict(orientation="h", y=-0.2),
    hovermode="x unified",
    height=400,
    )
    return fig

def margin_trend_chart(margins: list[dict]):
    """Stacked area chart of operating, EBITDA, net margins over time."""
    df = pd.DataFrame(margins)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["year"], y=df["ebitda_margin"],
    name="EBITDA Margin", fill="tozeroy",
    line=dict(color=BLUE)))
    fig.add_trace(go.Scatter(x=df["year"], y=df["operating_margin"],
    name="Operating Margin", fill="tozeroy",
    line=dict(color=GREEN)))
    fig.add_trace(go.Scatter(x=df["year"], y=df["net_margin"],
    name="Net Margin", fill="tozeroy",
    line=dict(color=ORANGE)))
    fig.update_layout(
    title="Margin Trends (%)", xaxis_title="Year",

    yaxis=dict(title="%", ticksuffix="%"),
    height=350, hovermode="x unified",
    )
    return fig
def cashflow_quality_chart(cf_data: dict):
    """Gauge chart for CFO/NP ratio with colour-coded quality zones."""
    ratio = cf_data.get("latest_cfo_np_ratio", 0) or 0
    color = GREEN if ratio >= 1.0 else BLUE if ratio >= 0.7 else ORANGE if ratio >= 0 else RED
    fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=ratio,
    title={"text": "CFO / Net Profit Ratio"},
    gauge={
    "axis": {"range": [-0.5, 2.0]},
    "bar": {"color": color},
    "steps": [
    {"range": [-0.5, 0], "color": "#fee2e2"},
    {"range": [0, 0.7], "color": "#fef3c7"},
    {"range": [0.7, 1.0],"color": "#dbeafe"},
    {"range": [1.0, 2.0],"color": "#dcfce7"},
    ],
    "threshold": {"line":{"color":"black","width":3},"value": 1.0},
    },
    delta={"reference": 1.0, "relative": False},
    ))
    fig.update_layout(height=300)
    return fig
def balance_bar_chart(balance_data: dict):
    """Horizontal bar chart showing D/E, current ratio, fixed asset ratio."""
    metrics = {
    "D/E Ratio": balance_data.get("de_ratio"),
    "Current Ratio": balance_data.get("current_ratio"),
    "Fixed Asset Ratio": balance_data.get("fixed_asset_ratio"),
    "CWIP Ratio": balance_data.get("cwip_ratio"),
    }
    labels = [k for k,v in metrics.items() if v is not None]
    values = [v for v in metrics.values() if v is not None]
    fig = go.Figure(go.Bar(
    x=values, y=labels, orientation="h",
    marker_color=[BLUE]*len(labels), text=[f"{v:.2f}" for v in values],
    textposition="outside",
    ))
    fig.update_layout(title="Balance Sheet Health (Latest Year)", height=280,
    xaxis_title="Ratio Value")
    return fig
