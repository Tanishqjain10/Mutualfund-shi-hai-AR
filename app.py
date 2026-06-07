# mutual_fund_dashboard/app.py
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

from funds_config import FUNDS
from data_fetcher import fetch_fund_data, get_nifty_returns, calculate_overlap

st.set_page_config(page_title="Live MF Dashboard", layout="wide")
st.title("🚀 Live Equity Mutual Fund Model Portfolio Dashboard")

# Live Status
col1, col2, col3, col4 = st.columns(4)
now = datetime.now()
with col1:
    st.metric("Last Updated", now.strftime("%Y-%m-%d %H:%M:%S"))
with col2:
    st.metric("Next Refresh", (now + timedelta(minutes=1)).strftime("%H:%M:%S"))
with col3:
    st.success("**Status: LIVE** ✅")
with col4:
    st.info("Data Source: VR + yfinance")

st_autorefresh(interval=60000, limit=1000, key="datarefresh")

# Fetch data
data = []
for fund in FUNDS:
    info = fetch_fund_data(fund.get("vr_id", 1000))
    row = {**fund, **info}
    data.append(row)

df = pd.DataFrame(data)

tabs = st.tabs(["Fund Overview", "Performance", "Risk", "Portfolio", "Overlap", "Benchmark", "Summary"])

with tabs[0]:
    cols = ['name', 'category', 'nav', 'aum', 'expense_ratio', 'fund_manager']
    st.dataframe(df[cols], use_container_width=True)

with tabs[1]:
    st.header("Performance Metrics")
    pcols = ['name', 'category', 'return_1M', 'return_3M', 'return_6M', 'return_1Y', 'return_3Y', 'return_5Y']
    st.dataframe(df[pcols], use_container_width=True)
    
    fig = px.bar(df, x='name', y='return_1Y', color='category', title="1Y Returns")
    st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.header("Risk Metrics")
    rcols = ['name', 'category', 'std_dev', 'beta', 'alpha']
    st.dataframe(df[rcols], use_container_width=True)

with tabs[3]:
    st.header("Portfolio Details")
    st.info("Holdings, flows & sector data from full VR scraper (extend fetch_fund_data)")

with tabs[4]:
    st.header("Overlap Analysis")
    overlap = calculate_overlap(df)
    st.write("Common Holdings:", overlap["common_holdings"])
    st.metric("Overlap Score", f"{overlap['overlap_score']}%")

with tabs[5]:
    st.header("Benchmark vs Nifty 50")
    nifty_1y = get_nifty_returns()
    st.metric("Nifty 50 1Y", f"{nifty_1y:.2f}%")
    
    fig_b = px.bar(df, x='name', y='return_1Y', title="Funds vs Nifty")
    fig_b.add_hline(y=nifty_1y, line_dash="dash", line_color="red", annotation_text="Nifty 50")
    st.plotly_chart(fig_b, use_container_width=True)

with tabs[6]:
    st.header("📊 Portfolio Summary (15th Section)")
    c1, c2, c3 = st.columns(3)
    with c1:
        aum_num = pd.to_numeric(df['aum'].str.extract(r'(\d+)')[0], errors='coerce').mean()
        st.metric("Avg AUM", f"{aum_num:.0f} Cr")
        exp_num = pd.to_numeric(df['expense_ratio'].str.extract(r'(\d+\.\d+)')[0], errors='coerce').mean()
        st.metric("Avg Expense", f"{exp_num:.2f}%")
    with c2:
        st.metric("Avg 1Y", f"{df['return_1Y'].mean():.1f}%")
        st.metric("Avg 3Y", f"{df['return_3Y'].mean():.1f}%")
    with c3:
        st.metric("Avg Alpha", f"{df['alpha'].mean():.1f}")
        health = round(df['return_1Y'].mean() * 0.6 + df['alpha'].mean() * 2.5 - df['std_dev'].mean() * 0.5, 1)
        st.success(f"**Health Score: {health}/100**")

csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Download Data", csv, "portfolio.csv", "text/csv")
