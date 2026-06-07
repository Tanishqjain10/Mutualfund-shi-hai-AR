# mutual_fund_dashboard/app.py
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
    st.info("Data Source: VR + AMFI + yfinance")

st_autorefresh(interval=60000, limit=1000, key="datarefresh")

# Fetch and flatten data
data = []
for fund in FUNDS:
    info = fetch_fund_data(fund["vr_id"])
    row = {**fund, **info}
    data.append(row)

df = pd.DataFrame(data)

# Overview Tabs
tabs = st.tabs(["Fund Overview", "Performance", "Risk", "Portfolio", "Overlap", "Benchmark", "Summary"])

with tabs[0]:
    overview_cols = ['name', 'category', 'nav', 'aum', 'expense_ratio', 'fund_manager']
    st.dataframe(df[overview_cols], use_container_width=True)

with tabs[1]:
    st.header("Performance Metrics")
    perf_df = df[['name', 'category', 'return_1M', 'return_3M', 'return_6M', 'return_1Y', 'return_3Y', 'return_5Y']]
    st.dataframe(perf_df, use_container_width=True)
    
    # Performance Chart
    fig_perf = px.bar(df, x='name', y='return_1Y', color='category', 
                      title="1 Year Returns Comparison", 
                      color_discrete_sequence=px.colors.sequential.Blues)
    st.plotly_chart(fig_perf, use_container_width=True)

with tabs[2]:
    st.header("Risk Metrics")
    risk_df = df[['name', 'category', 'std_dev', 'beta', 'alpha']]
    st.dataframe(risk_df, use_container_width=True)

with tabs[3]:
    st.header("Portfolio Details")
    st.info("Top holdings, sector allocation & flows would be parsed from #fund-portfolio sections")

with tabs[4]:
    st.header("Overlap Analysis")
    overlap = calculate_overlap(df.to_dict('records'))
    st.write("Common Holdings:", overlap["common_holdings"])
    st.metric("Portfolio Overlap Score", f"{overlap['overlap_score']}%")

with tabs[5]:
    st.header("Benchmark Comparison (Nifty 50)")
    nifty_1y = get_nifty_returns()
    st.metric("Nifty 50 - 1Y Return", f"{nifty_1y}%")
    
    fig_bench = px.bar(df, x='name', y='return_1Y', 
                       title="Fund vs Nifty 1Y Returns",
                       color_discrete_sequence=['#1f77b4'])
    fig_bench.add_hline(y=nifty_1y, line_dash="dash", annotation_text="Nifty 50")
    st.plotly_chart(fig_bench, use_container_width=True)

with tabs[6]:
    st.header("📊 15th Section: Portfolio Summary")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        st.metric("Avg AUM", f"{df['aum'].str.extract('(\d+)').astype(float).mean():.0f} Cr")
        st.metric("Avg Expense Ratio", f"{df['expense_ratio'].str.extract('(\d+\.\d+)').astype(float).mean():.2f}%")
    
    with col_b:
        st.metric("Avg 1Y Return", f"{df['return_1Y'].mean():.1f}%")
        st.metric("Avg 3Y CAGR", f"{df['return_3Y'].mean():.1f}%")
    
    with col_c:
        st.metric("Avg Std Dev", f"{df['std_dev'].mean():.1f}")
        st.metric("Avg Alpha", f"{df['alpha'].mean():.1f}")
    
    health_score = round((df['return_1Y'].mean() * 0.4) + (df['alpha'].mean() * 2) - (df['std_dev'].mean() * 0.3), 1)
    st.success(f"**Overall Portfolio Health Score: {health_score}/100**")

# Download
csv = df.to_csv(index=False).encode()
st.download_button("Download Full Portfolio Data", csv, "portfolio_data.csv", "text/csv")
