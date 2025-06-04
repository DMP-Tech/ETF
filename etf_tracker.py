import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import plotly.graph_objs as go
import numpy as np
from sklearn.linear_model import LinearRegression

# ------------------ Configuration ------------------
st.set_page_config(page_title="ETF Strategy Tracker", layout="wide")

# ------------------ Styling ------------------
st.markdown("""
    <style>
    .main-header {
        background-color: #1f4e79;
        padding: 1rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 0;
        position: relative;
    }
    .ticker-text {
        font-size: 1.3rem;
        font-weight: bold;
        color: white;
        white-space: nowrap;
        overflow: hidden;
        box-sizing: border-box;
    }
    .ticker-text span {
        display: inline-block;
        padding-left: 100%;
        animation: scroll-left 20s linear infinite;
    }
    @keyframes scroll-left {
        0% { transform: translateX(0%); }
        100% { transform: translateX(-100%); }
    }
    .price-bar {
        background-color: #003366;
        color: white;
        font-size: 0.85rem;
        padding: 5px 0;
        white-space: nowrap;
        overflow: hidden;
        margin-bottom: 1.5rem;
        border-radius: 0 0 12px 12px;
    }
    .price-bar span {
        display: inline-block;
        padding-left: 100%;
        animation: scroll-left 25s linear infinite;
    }
    </style>
""", unsafe_allow_html=True)

# ------------------ ETF List ------------------
indian_etfs = [
    "NIFTYBEES.NS", "BANKBEES.NS", "PSUBNKBEES.NS", "ICICINIFTY.NS", "KOTAKNIFTY.NS",
    "HDFCNIFTY.NS", "UTINIFTETF.NS", "SBINIFTY.NS", "AXISNIFTY.NS", "M50.NS",
    "M100.NS", "N100.NS", "NETFCONSUM.NS", "NETFDIVOPP.NS", "GOLDBEES.NS",
    "HNGSNGBEES.NS", "KOTAKPSUBK.NS", "LICNETFN50.NS", "LICNETFSEN.NS",
    "MAN50ETF.NS", "MANXT50.NS", "MAFANG.NS", "CPSEETF.NS", "BHARATIWIN.NS"
]

# ------------------ Live ETF Prices ------------------
@st.cache_data(ttl=900)
def get_etf_prices(etfs):
    prices = []
    for etf in etfs:
        try:
            data = yf.Ticker(etf).history(period="1d")
            if not data.empty:
                last_price = round(data["Close"].iloc[-1], 2)
                prices.append(f"{etf.replace('.NS', '')}: ₹{last_price}")
        except:
            pass
    return " | ".join(prices)

# ------------------ Header + Ticker ------------------
st.markdown('<div class="main-header"><div class="ticker-text"><span>📈 Indian ETF Buy/Sell Strategy | Track live signals & opportunities 📊</span></div></div>', unsafe_allow_html=True)
live_prices = get_etf_prices(indian_etfs)
st.markdown(f'<div class="price-bar"><span>{live_prices}</span></div>', unsafe_allow_html=True)

# ------------------ ETF Strategy Logic ------------------
tab1, tab2, tab3 = st.tabs(["🛒 Buy Candidates", "📈 Sell Monitor", "📘 ETF Insights"])

# Helper
@st.cache_data(ttl=900)
def fetch_etf_data(ticker):
    return yf.Ticker(ticker).history(period="1y")

with tab1:
    st.subheader("🧨 ETFs At 52-Week Low or Below")
    low_df = []
    for etf in indian_etfs:
        df = fetch_etf_data(etf)
        if df.empty: continue
        low_52 = df['Low'].min()
        last_price = df['Close'].iloc[-1]
        if last_price <= low_52:
            low_df.append({"ETF": etf.replace(".NS", ""), "Current Price": round(last_price,2), "52-Week Low": round(low_52,2)})
    if low_df:
        st.dataframe(pd.DataFrame(low_df))
    else:
        st.info("No ETFs at 52-week low currently.")

with tab2:
    st.subheader("📈 Track ETFs for 5% Target")
    buy_file = "buy_list.csv"
    if os.path.exists(buy_file):
        buys = pd.read_csv(buy_file)
        updates = []
        for idx, row in buys.iterrows():
            current_price = yf.Ticker(row['ETF'] + ".NS").history(period="1d")['Close'].iloc[-1]
            target = row['Buy Price'] * 1.05
            hit_target = "✅" if current_price >= target else "❌"
            updates.append({"ETF": row['ETF'], "Buy Price": row['Buy Price'], "Current": round(current_price,2), "Target": round(target,2), "Hit Target": hit_target})
        st.dataframe(pd.DataFrame(updates))
    else:
        st.warning("No buy list found. Add ETFs manually to track.")

with tab3:
    st.subheader("📘 ETF Chart & Price Prediction")
    selected_etf = st.selectbox("Select ETF to Analyze", indian_etfs)
    hist = fetch_etf_data(selected_etf)
    if not hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close']))
        fig.update_layout(title=f"{selected_etf.replace('.NS','')} - 1Y Candlestick Chart", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True)

        # Prediction (simple linear regression)
        hist = hist.reset_index()
        hist['Date_Ordinal'] = hist['Date'].map(datetime.toordinal)
        X = hist[['Date_Ordinal']]
        y = hist['Close']
        model = LinearRegression().fit(X, y)
        future_days = 30
        future = pd.date_range(start=hist['Date'].iloc[-1], periods=future_days)
        future_df = pd.DataFrame({"Date": future})
        future_df['Date_Ordinal'] = future_df['Date'].map(datetime.toordinal)
        future_df['Prediction'] = model.predict(future_df[['Date_Ordinal']])

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=hist['Date'], y=hist['Close'], name="Historical"))
        fig2.add_trace(go.Scatter(x=future_df['Date'], y=future_df['Prediction'], name="30-Day Forecast", line=dict(dash="dot")))
        fig2.update_layout(title=f"{selected_etf.replace('.NS','')} - 30 Day Price Prediction", xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Data not available for selected ETF.")
