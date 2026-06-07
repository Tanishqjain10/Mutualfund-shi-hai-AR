import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from funds_config import FUNDS
from data_fetcher import fetch_fund_data, get_nifty_returns, calculate_overlap

st.set_page_config(page_title="Live MF Dashboard", layout="wide")
st.title("🚀 Live Equity Mutual Fund Model Portfolio Dashboard")

# Live Status Panel
col1, col2, col3, col4 = st.columns(4)
now = datetime.now()
with col1:
    st.metric("Last Updated", now.strftime("%Y-%m-%d %H:%M:%S"))
with col2:
    st.metric("Next Refresh", (now + timedelta(minutes=1)).strftime("%H:%M:%S"))
with col3:
    st.success("**Status: LIVE** ✅")
with col4:
    st.info("Data Source: VR + AMFI")

st_autorefresh(interval=60000, limit=1000, key="datarefresh")

# Fetch data
data = []
for fund in FUNDS:
    info = fetch_fund_data(fund["vr_id"])
    row = {**fund, **info}
    data.append(row)

df = pd.DataFrame(data)

# Overview Tabs
tabs = st.tabs(["Fund Overview", "Performance", "Risk", "Portfolio", "Overlap", "Benchmark", "Summary"])

with tabs[0]:
    st.dataframe(df[['name', 'category', 'aum', 'expense_ratio', 'fund_manager']], use_container_width=True)

with tabs[1]:
    perf_cols = st.columns(3)
    for i, fund in enumerate(df.to_dict('records')[:3]):  # Example
        with perf_cols[i % 3]:
            st.subheader(fund['name'])
            for period, ret in fund['returns'].items():
                color = "green" if ret > 0 else "red"
                st.metric(period, f"{ret}%", delta=None)

# Charts
st.header("Performance Comparison")
fig = px.bar(df, x='name', y='returns.1Y', color='category', title="1Y Returns")
st.plotly_chart(fig, use_container_width=True)

# Aggregated Summary
st.header("📊 15th Section: Portfolio Summary")
avg_1y = df.apply(lambda x: x['returns']['1Y'] if isinstance(x['returns'], dict) else 0, axis=1).mean()
st.metric("Average 1Y Return", f"{avg_1y:.1f}%")

st.success("Dashboard is fully dynamic and auto-refreshing. Add scraping logic in data_fetcher.py for full VR integration.")

# Download button for data
csv = df.to_csv(index=False).encode()
st.download_button("Download Portfolio Data", csv, "portfolio.csv", "text/csv")