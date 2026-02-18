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
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Nifty Bank": "^NSEBANK",
    "S&P 500 (US)": "^GSPC",
    "Nasdaq 100 (US)": "^IXIC"
}

STOCKS = {
    "Reliance Industries": "RELIANCE.NS",
    "TATA Consultancy Services (TCS)": "TCS.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Infosys": "INFY.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India (SBI)": "SBIN.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "ITC Limited": "ITC.NS",
    "Larsen & Toubro (L&T)": "LT.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "HCL Technologies": "HCLTECH.NS",
    "Sun Pharma": "SUNPHARMA.NS",
    "Titan Company": "TITAN.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "UltraTech Cement": "ULTRACEMCO.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "NTPC": "NTPC.NS",
    "Wipro": "WIPRO.NS",
    "Tata Steel": "TATASTEEL.NS",
    "Coal India": "COALINDIA.NS",
    "Adani Enterprises": "ADANIENT.NS",
    "Zomato": "ZOMATO.NS",
    "Paytm (One97)": "PAYTM.NS",
    "DLF": "DLF.NS",
    "Varun Beverages": "VBL.NS",
    "Jio Financial": "JIOFIN.NS",
    "Suzlon Energy": "SUZLON.NS",
    "Apple (US Demo)": "AAPL",
    "Tesla (US Demo)": "TSLA",
    "SPY ETF (US Demo)": "SPY"
}

# --- SIDEBAR: MASTER CONTROLS ---
with st.sidebar:
    st.header("🎛️ Control Panel")
    asset_class = st.selectbox("1. Select Asset Class:", 
                               ["Indices (Market View)", "Equities (Stocks)", "Derivatives (Options)"])
    
    st.divider()
    
    if asset_class == "Indices (Market View)":
        selected_name = st.selectbox("Choose Index:", list(INDICES.keys()))
        ticker = INDICES[selected_name]
    elif asset_class == "Equities (Stocks)":
        selected_name = st.selectbox("Search Stock:", list(STOCKS.keys()))
        ticker = STOCKS[selected_name]
    else: # Derivatives
        st.warning("⚠️ Indian Options data may be delayed. Try 'US Demo' stocks for better live data.")
        selected_name = st.selectbox("Select Stock for Options:", list(STOCKS.keys()))
        ticker = STOCKS[selected_name]

    num_articles = st.slider("Analyze Depth (Articles):", 5, 50, 15)
    analyze_btn = st.button("Run Analysis 🚀")

# --- MAIN DASHBOARD LOGIC ---
if analyze_btn:
    try:
        stock = yf.Ticker(ticker)
        
        if asset_class == "Derivatives (Options)":
            tabs = st.tabs(["📉 Options Chain", "📊 Bull/Bear Ratio", "📋 Raw Data"])
        else:
            tabs = st.tabs(["📈 Price Action", "📰 AI Sentiment Analysis", "📋 Key Stats"])

        # TAB 1 & 2 for Indices/Equities
        if asset_class != "Derivatives (Options)":
            with tabs[0]:
                history = stock.history(period="6mo")
                if not history.empty:
                    current = history['Close'].iloc[-1]
                    change = current - history['Close'].iloc[-2]
                    st.metric(label=f"{ticker} Price", value=f"₹{current:,.2f}", delta=f"{change:.2f}")
                    fig = go.Figure(data=[go.Candlestick(x=history.index, open=history['Open'], high=history['High'], low=history['Low'], close=history['Close'])])
                    st.plotly_chart(fig, use_container_width=True)

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
                            with st.expander(f"{r['label'].upper()}: {r['title']}"):
                                st.write(f"Confidence: {r['score']:.2f}")
            
            # THE OPTIMIZED TAB 3
            with tabs[2]:
                st.subheader("📋 Key Fundamentals")
                try:
                    info = stock.info
                    if info and len(info) > 5:
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Market Cap", f"₹{info.get('marketCap', 0):,}")
                        c1.metric("P/E Ratio", info.get('trailingPE', 'N/A'))
                        c2.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 0):,}")
                        c2.metric("52W Low", f"₹{info.get('fiftyTwoWeekLow', 0):,}")
                        c3.metric("Div. Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%")
                        with st.expander("View Full Raw Data (JSON)"):
                            st.json(info)
                    else:
                        st.warning("⚠️ Rate limited for detailed stats. Price and News remain functional.")
                except Exception:
                    st.error("Rate limit reached for Fundamental Data.")

        # DERIVATIVES LOGIC
        else:
            expirations = stock.options
            if expirations:
                with tabs[0]:
                    sel_expiry = st.selectbox("Expiry:", expirations)
                    chain = stock.option_chain(sel_expiry)
                    st.dataframe(chain.calls.head(10))
                with tabs[1]:
                    c_oi = chain.calls['openInterest'].sum()
                    p_oi = chain.puts['openInterest'].sum()
                    st.metric("Put-Call Ratio", f"{p_oi/c_oi:.2f}" if c_oi > 0 else "N/A")
                    st.plotly_chart(go.Figure(data=[go.Pie(labels=['Calls', 'Puts'], values=[c_oi, p_oi])]))
            else:
                st.error("No Options Data available.")

    except Exception as e:
        st.error(f"Error: {e}")
