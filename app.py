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
INDICES = {
    "Nifty 50": "^NSEI", "Sensex": "^BSESN", "Nifty Bank": "^NSEBANK", "S&P 500": "^GSPC"
}
STOCKS = {
    "Reliance Industries": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS", "Zomato": "ZOMATO.NS", "Tata Motors": "TATAMOTORS.NS"
}

# --- SIDEBAR: MASTER CONTROLS ---
with st.sidebar:
    st.header("🎛️ Control Panel")
    asset_class = st.selectbox("1. Select Asset Class:", ["Equities (Stocks)", "Indices (Market View)", "Derivatives (Options)"])
    
    st.divider()
    
    # --- DYNAMIC DROPDOWN LOGIC ---
    st.subheader("2. Select Instrument")
    
    # Switch the list based on Asset Class
    if asset_class == "Indices (Market View)":
        current_list = INDICES
    else:
        current_list = STOCKS
        
    dropdown_name = st.selectbox("Choose from list:", list(current_list.keys()))
    dropdown_ticker = current_list[dropdown_name]
    
    # --- MANUAL OVERRIDE ---
    manual_ticker = st.text_input("OR Type Any Ticker (e.g. SUZLON.NS):", "")
    
    # Final Ticker selection logic
    ticker = manual_ticker.upper() if manual_ticker else dropdown_ticker
    
    st.info(f"Target: **{ticker}**")
    num_articles = st.slider("Analyze Depth (Articles):", 5, 50, 15)
    analyze_btn = st.button("Run Analysis 🚀")

# --- MAIN DASHBOARD LOGIC ---
if analyze_btn:
    try:
        stock = yf.Ticker(ticker)
        tabs = st.tabs(["📈 Price Action", "📰 AI Sentiment Analysis", "📋 Key Stats"])

        # --- TAB 1: PRICE ACTION ---
        with tabs[0]:
            history = stock.history(period="6mo")
            if not history.empty:
                # Use a separate try block for info to keep Price Action alive
                try:
                    info = stock.info
                    current = info.get('currentPrice') or history['Close'].iloc[-1]
                    prev_close = info.get('previousClose') or history['Close'].iloc[-2]
                except:
                    current = history['Close'].iloc[-1]
                    prev_close = history['Close'].iloc[-2]

                change = current - prev_close
                pct_change = (change / prev_close) * 100

                # Main Display
                st.metric(label=f"{ticker} Price", value=f"₹{current:,.2f}", delta=f"{change:.2f} ({pct_change:.2f}%)")
                
                # The Technical Row
                t1, t2, t3, t4 = st.columns(4)
                try:
                    t1.metric("Open", f"₹{info.get('open', 'N/A')}")
                    t2.metric("Day High", f"₹{info.get('dayHigh', 'N/A')}")
                    t3.metric("Day Low", f"₹{info.get('dayLow', 'N/A')}")
                    t4.metric("Prev. Close", f"₹{prev_close:,.2f}")
                except:
                    st.caption("Detailed technicals temporarily unavailable (API Rate Limit).")

                # Candlestick
                fig = go.Figure(data=[go.Candlestick(x=history.index, open=history['Open'], high=history['High'], low=history['Low'], close=history['Close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, height=500, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No price data found.")

        # --- TAB 2: SENTIMENT ---
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
                    c1.metric("Positive", pos)
                    c2.metric("Negative", neg)
                    c3.metric("Mood", "BULLISH 🐂" if pos > neg else "BEARISH 🐻")
                    for r in results:
                        emoji = "🟢" if r['label'] == 'positive' else "🔴" if r['label'] == 'negative' else "⚪"
                        with st.expander(f"{emoji} {r['label'].upper()}: {r['title']}"):
                            st.write(f"AI Confidence: {r['score']:.2f}")

        # --- TAB 3: KEY STATS (Fail-Safe) ---
        with tabs[2]:
            st.subheader("📋 Fundamental Data")
            try:
                info = stock.info
                if info and len(info) > 10:
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Market Cap", f"₹{info.get('marketCap', 0):,}")
                    k1.metric("P/E Ratio", info.get('trailingPE', 'N/A'))
                    k2.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 0):,}")
                    k2.metric("52W Low", f"₹{info.get('fiftyTwoWeekLow', 0):,}")
                    k3.metric("Div. Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%")
                    k3.metric("Volume", f"{info.get('averageVolume', 0):,}")
                    with st.expander("Raw Data"):
                        st.json(info)
                else:
                    st.warning("API is currently limiting detailed stats. Price and News are still fully functional.")
            except:
                st.error("Fundamental Data is temporarily locked by the API provider.")

    except Exception as e:
        st.error(f"Critical Error: {e}")
