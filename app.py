import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from transformers import pipeline

# 1. Page Configuration
st.set_page_config(page_title="Market Analyzer Pro", page_icon="📊", layout="wide")
st.title("📊 Overall Market Analyzer")

# --- Load AI Model (Cached) ---
@st.cache_resource
def load_model():
    return pipeline("text-classification", model="ProsusAI/finbert")

with st.spinner("Initializing AI Engines..."):
    pipe = load_model()

# --- DATA: The Master Lists ---
STOCKS = {
    "Reliance Industries": "RELIANCE.NS", "TCS.NS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS", "ICICI Bank": "ICICIBANK.NS", "Zomato": "ZOMATO.NS",
    "Tata Motors": "TATAMOTORS.NS", "Paytm": "PAYTM.NS", "Apple (US Demo)": "AAPL"
}

# --- SIDEBAR: MASTER CONTROLS ---
with st.sidebar:
    st.header("🎛️ Control Panel")
    asset_class = st.selectbox("1. Select Asset Class:", ["Equities (Stocks)", "Indices (Market View)", "Derivatives (Options)"])
    
    st.divider()
    
    # --- DUAL SEARCH SYSTEM ---
    st.subheader("2. Select or Search")
    dropdown_ticker = st.selectbox("Choose from list:", list(STOCKS.keys()))
    manual_ticker = st.text_input("OR Type Any Ticker (e.g. VEDL.NS):", "")
    
    ticker = manual_ticker.upper() if manual_ticker else STOCKS[dropdown_ticker]
    
    num_articles = st.slider("Analyze Depth (Articles):", 5, 50, 15)
    analyze_btn = st.button("Run Analysis 🚀")

# --- MAIN DASHBOARD LOGIC ---
if analyze_btn:
    try:
        stock = yf.Ticker(ticker)
        
        # Tabs for better organization
        tabs = st.tabs(["📈 Price Action", "📰 AI Sentiment Analysis", "📋 Key Stats"])

        # --- TAB 1: PRICE ACTION (Restored Metrics) ---
        with tabs[0]:
            history = stock.history(period="6mo")
            if not history.empty:
                # Fetch Latest Detailed Prices
                info = stock.info
                current = info.get('currentPrice') or history['Close'].iloc[-1]
                prev_close = info.get('previousClose') or history['Close'].iloc[-2]
                change = current - prev_close
                pct_change = (change / prev_close) * 100

                # Main Price Delta
                st.metric(label=f"{ticker} Live Price", value=f"₹{current:,.2f}", delta=f"{change:.2f} ({pct_change:.2f}%)")
                
                # RE-ADDED: Technical Metrics Grid
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Open", f"₹{info.get('open', 'N/A'):,}")
                m2.metric("Day High", f"₹{info.get('dayHigh', 'N/A'):,}")
                m3.metric("Day Low", f"₹{info.get('dayLow', 'N/A'):,}")
                m4.metric("Prev. Close", f"₹{prev_close:,.2f}")

                # Candlestick Chart
                fig = go.Figure(data=[go.Candlestick(x=history.index, open=history['Open'], high=history['High'], low=history['Low'], close=history['Close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, height=500)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No price data available for this ticker.")

        # --- TAB 2: SENTIMENT ANALYSIS ---
        with tabs[1]:
            news = stock.news
            if news:
                results = []
                prog = st.progress(0)
                for i, art in enumerate(news[:num_articles]):
                    prog.progress((i+1)/len(news[:num_articles]))
                    story = art.get('content', {})
                    if story.get('summary'):
                        res = pipe(story['summary'])[0]
                        results.append({"title": story['title'], "label": res['label'], "score": res['score']})
                prog.empty()
                
                if results:
                    pos = sum(1 for r in results if r['label'] == 'positive')
                    neg = sum(1 for r in results if r['label'] == 'negative')
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Positive Articles", pos)
                    c2.metric("Negative Articles", neg)
                    c3.metric("Overall Mood", "BULLISH 🐂" if pos > neg else "BEARISH 🐻")
                    for r in results:
                        emoji = "🟢" if r['label'] == 'positive' else "🔴" if r['label'] == 'negative' else "⚪"
                        with st.expander(f"{emoji} {r['label'].upper()}: {r['title']}"):
                            st.write(f"Confidence Score: {r['score']:.2f}")

        # --- TAB 3: KEY STATS (Final Resilience Fix) ---
        with tabs[2]:
            st.subheader("📋 Fundamental Data")
            try:
                # Optimized info retrieval
                info = stock.info
                if info and len(info) > 10:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Market Cap", f"₹{info.get('marketCap', 0):,}")
                    c1.metric("P/E Ratio", info.get('trailingPE', 'N/A'))
                    c2.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 0):,}")
                    c2.metric("52W Low", f"₹{info.get('fiftyTwoWeekLow', 0):,}")
                    c3.metric("Div. Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%")
                    c3.metric("Avg Volume", f"{info.get('averageVolume', 0):,}")
                    with st.expander("View Raw Data Details"):
                        st.json(info)
                else:
                    st.warning("⚠️ Yahoo Finance is currently throttling detailed stats. Please wait 60 seconds.")
            except:
                st.error("Fundamental Data could not be loaded at this time.")

    except Exception as e:
        st.error(f"Error initializing analysis: {e}")
