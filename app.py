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
    info = fetch_fund_data(fund.get("vr_id", 1000))
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
    perf_cols = ['name', 'category', 'return_1M', 'return_3M', 'return_6M', 'return_1Y', 'return_3Y', 'return_5Y']
    st.dataframe(df[perf_cols], use_container_width=True)
    
    fig_perf = px.bar(df, x='name', y='return_1Y', color='category', 
                      title="1 Year Returns by Fund",
                      color_discrete_sequence=px.colors.sequential.Viridis)
    st.plotly_chart(fig_perf, use_container_width=True)

with tabs[2]:
    st.header("Risk Metrics")
    risk_cols = ['name', 'category', 'std_dev', 'beta', 'alpha']
    st.dataframe(df[risk_cols], use_container_width=True)

with tabs[3]:
    st.header("Portfolio Details")
    st.info("🔄 Top 10 Holdings, Sector Allocation & Flows parsed from #fund-portfolio URLs (extend scraper)")

with tabs[4]:
    st.header("Overlap Analysis")
    overlap = calculate_overlap(df.to_dict('records'))
    st.write("**Common Holdings Across Portfolio**:", overlap["common_holdings"])
    st.metric("Overall Overlap Score", f"{overlap['overlap_score']}%")

with tabs[5]:
    st.header("Benchmark Comparison (vs Nifty 50)")
    nifty_1y = get_nifty_returns()
    st.metric("Nifty 50 1Y Return", f"{float(nifty_1y):.2f}%")
    
    fig_bench = px.bar(df, x='name', y='return_1Y', title="Funds vs Nifty 50 (1Y)")
    fig_bench.add_hline(y=float(nifty_1y), line_dash="dash", line_color="red", annotation_text="Nifty 50")
    st.plotly_chart(fig_bench, use_container_width=True)

with tabs[6]:
    st.header("📊 15th Section: Aggregated Portfolio Summary")
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        avg_aum = pd.to_numeric(df['aum'].str.extract(r'(\d+)').iloc[:, 0], errors='coerce').mean()
        st.metric("Average AUM", f"{avg_aum:.0f if not pd.isna(avg_aum) else 0} Cr")
        avg_exp = pd.to_numeric(df['expense_ratio'].str.extract(r'(\d+\.\d+)').iloc[:, 0], errors='coerce').mean()
        st.metric("Average Expense Ratio", f"{avg_exp:.2f if not pd.isna(avg_exp) else 0}%")
    
    with col_b:
        st.metric("Avg 1Y Return", f"{df['return_1Y'].mean():.1f}%")
        st.metric("Avg 3Y CAGR", f"{df['return_3Y'].mean():.1f}%")
        st.metric("Avg 5Y CAGR", f"{df['return_5Y'].mean():.1f}%")
    
    with col_c:
        st.metric("Avg Std Dev", f"{df['std_dev'].mean():.1f}")
        st.metric("Avg Beta", f"{df['beta'].mean():.2f}")
        st.metric("Avg Alpha", f"{df['alpha'].mean():.1f}")
    
    health_score = round(df['return_1Y'].mean() * 0.5 + df['alpha'].mean() * 3 - df['std_dev'].mean() * 0.4, 1)
    st.success(f"**Overall Portfolio Health Score: {health_score} / 100**")

# Download
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Full Portfolio Data", csv, "portfolio_data.csv", "text/csv")
