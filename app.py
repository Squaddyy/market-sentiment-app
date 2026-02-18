import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from transformers import pipeline

# 1. Page Configuration & Custom CSS for Design
st.set_page_config(page_title="Market Analyzer Pro", page_icon="📊", layout="wide")

# Custom CSS for that "Premium" look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    footer {visibility: hidden;}
    .css-1d391kg { background-image: linear-gradient(#2e3b4e, #1c2531); color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Overall Market Analyzer")

# --- Load AI Model (Cached) ---
@st.cache_resource
def load_model():
    return pipeline("text-classification", model="ProsusAI/finbert")

with st.spinner("Initializing AI Engines..."):
    pipe = load_model()

# --- THE MEGA LIST (Expanded for Dropdown) ---
INDICES = {
    "Nifty 50": "^NSEI", "Sensex": "^BSESN", "Nifty Bank": "^NSEBANK", "Nifty IT": "^CNXIT", "S&P 500": "^GSPC"
}

STOCKS = {
    "Reliance Industries": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS", "ICICI Bank": "ICICIBANK.NS", "Hindustan Unilever": "HINDUNILVR.NS",
    "SBI": "SBIN.NS", "Bharti Airtel": "BHARTIARTL.NS", "ITC": "ITC.NS", "L&T": "LT.NS",
    "Bajaj Finance": "BAJFINANCE.NS", "Axis Bank": "AXISBANK.NS", "Kotak Bank": "KOTAKBANK.NS",
    "Adani Ent": "ADANIENT.NS", "Tata Motors": "TATAMOTORS.NS", "Sun Pharma": "SUNPHARMA.NS",
    "Maruti": "MARUTI.NS", "NTPC": "NTPC.NS", "Titan": "TITAN.NS", "Zomato": "ZOMATO.NS",
    "Paytm": "PAYTM.NS", "Jio Financial": "JIOFIN.NS", "Suzlon": "SUZLON.NS", "Vedanta": "VEDL.NS",
    "Yes Bank": "YESBANK.NS", "Tata Steel": "TATASTEEL.NS", "Wipro": "WIPRO.NS", "Coal India": "COALINDIA.NS",
    "Asian Paints": "ASIANPAINT.NS", "M&M": "M&M.NS", "Power Grid": "POWERGRID.NS", "HCL Tech": "HCLTECH.NS"
}

# --- SIDEBAR: MASTER CONTROLS ---
with st.sidebar:
    st.header("🎛️ Control Panel")
    asset_class = st.selectbox("1. Select Asset Class:", ["Equities (Stocks)", "Indices (Market View)", "Derivatives (Options)"])
    
    st.divider()
    st.subheader("2. Select Instrument")
    
    # Dynamic List Selection
    current_list = INDICES if asset_class == "Indices (Market View)" else STOCKS
    
    # Sort keys for easier navigation
    sorted_keys = sorted(list(current_list.keys()))
    dropdown_name = st.selectbox("Choose from list:", sorted_keys)
    dropdown_ticker = current_list[dropdown_name]
    
    manual_ticker = st.text_input("OR Type Any Ticker (e.g. IRFC.NS):", "")
    ticker = manual_ticker.upper() if manual_ticker else dropdown_ticker
    
    st.info(f"Target: **{ticker}**")
    num_articles = st.slider("Analyze Depth (Articles):", 5, 50, 15)
    
    analyze_btn = st.button("Run Analysis 🚀", use_container_width=True)
    
    # THE SIGNATURE
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🛠️ Built by **Squaddyy**")
    st.caption("AI-Powered Financial Intelligence v2.0")

# --- MAIN DASHBOARD LOGIC ---
if analyze_btn:
    try:
        stock = yf.Ticker(ticker)
        tabs = st.tabs(["📈 Price Action", "📰 AI Sentiment Analysis", "📋 Key Stats"])

        with tabs[0]:
            history = stock.history(period="6mo")
            if not history.empty:
                try:
                    info = stock.info
                    current = info.get('currentPrice') or history['Close'].iloc[-1]
                    prev_close = info.get('previousClose') or history['Close'].iloc[-2]
                except:
                    current = history['Close'].iloc[-1]
                    prev_close = history['Close'].iloc[-2]

                change = current - prev_close
                pct_change = (change / prev_close) * 100

                st.metric(label=f"{ticker} Live Price", value=f"₹{current:,.2f}", delta=f"{change:.2f} ({pct_change:.2f}%)")
                
                t1, t2, t3, t4 = st.columns(4)
                t1.metric("Open", f"₹{info.get('open', 'N/A')}")
                t2.metric("Day High", f"₹{info.get('dayHigh', 'N/A')}")
                t3.metric("Day Low", f"₹{info.get('dayLow', 'N/A')}")
                t4.metric("Prev. Close", f"₹{prev_close:,.2f}")

                fig = go.Figure(data=[go.Candlestick(x=history.index, open=history['Open'], high=history['High'], low=history['Low'], close=history['Close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, height=550, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        with tabs[1]:
            news = stock.news
            if news:
                results = []
                prog = st.progress(0)
                articles_to_process = news[:num_articles]
                for i, art in enumerate(articles_to_process):
                    prog.progress((i+1)/len(articles_to_process))
                    story = art.get('content', {})
                    if story.get('summary'):
                        res = pipe(story['summary'])[0]
                        results.append({"title": story['title'], "label": res['label'], "score": res['score']})
                prog.empty()
                
                if results:
                    pos = sum(1 for r in results if r['label'] == 'positive')
                    neg = sum(1 for r in results if r['label'] == 'negative')
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Positive", pos, "Trend Up" if pos > neg else None)
                    c2.metric("Negative", neg, "Trend Down" if neg > pos else None, delta_color="inverse")
                    c3.metric("Mood", "BULLISH 🐂" if pos > neg else "BEARISH 🐻")
                    
                    for r in results:
                        emoji = "🟢" if r['label'] == 'positive' else "🔴" if r['label'] == 'negative' else "⚪"
                        with st.expander(f"{emoji} {r['label'].upper()}: {r['title']}"):
                            st.write(f"AI Confidence: {r['score']:.2f}")

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
                else:
                    st.warning("API Throttling: Key stats currently unavailable. Price/News are safe.")
            except:
                st.error("Fundamental Data temporarily offline.")

    except Exception as e:
        st.error(f"Analysis Error: {e}")
