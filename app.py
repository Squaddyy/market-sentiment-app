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

# The Top 50+ Most Popular Stocks
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
    # US Stocks for Demo (Reliable Options Data)
    "Apple (US Demo)": "AAPL",
    "Tesla (US Demo)": "TSLA",
    "SPY ETF (US Demo)": "SPY"
}

# --- SIDEBAR: MASTER CONTROLS ---
with st.sidebar:
    st.header("🎛️ Control Panel")
    
    # LEVEL 1: Asset Class
    asset_class = st.selectbox("1. Select Asset Class:", 
                               ["Indices (Market View)", "Equities (Stocks)", "Derivatives (Options)"])
    
    st.divider()
    
    # LEVEL 2: Specific Instrument (Dynamic Dropdowns)
    if asset_class == "Indices (Market View)":
        st.subheader("2. Select Index")
        selected_name = st.selectbox("Choose Index:", list(INDICES.keys()))
        ticker = INDICES[selected_name]
        st.info(f"Analyzing: **{selected_name}**")
        
    elif asset_class == "Equities (Stocks)":
        st.subheader("2. Select Stock")
        # Dropdown with search
        selected_name = st.selectbox("Search Stock:", list(STOCKS.keys()))
        ticker = STOCKS[selected_name]
        st.info(f"Analyzing: **{selected_name}**")

    else: # Derivatives
        st.subheader("2. Select Underlying Asset")
        st.warning("⚠️ Note: Indian Options data may be delayed/empty on free APIs. Use 'US Demo' stocks to see full charts.")
        
        # We reuse the STOCK list for derivatives
        selected_name = st.selectbox("Select Stock for Options:", list(STOCKS.keys()))
        ticker = STOCKS[selected_name]
        st.info(f"Fetching Options for: **{selected_name}**")

    st.divider()
    analyze_btn = st.button("Run Analysis 🚀")

# --- MAIN DASHBOARD LOGIC ---
if analyze_btn:
    try:
        stock = yf.Ticker(ticker)
        
        # --- TAB SYSTEM ---
        if asset_class == "Derivatives (Options)":
            tabs = st.tabs(["📉 Options Chain", "📊 Bull/Bear Ratio", "📋 Raw Data"])
        else:
            tabs = st.tabs(["📈 Price Action", "📰 AI Sentiment Analysis", "📋 Key Stats"])

        # ==========================================
        # LOGIC FOR INDICES & EQUITIES
        # ==========================================
        if asset_class != "Derivatives (Options)":
            
            # TAB 1: PRICE
            with tabs[0]:
                st.subheader(f"Price Trend: {ticker}")
                # Fetch more history for indices to show better trends
                history = stock.history(period="6mo")
                
                if not history.empty:
                    # Get Current Price safely
                    current_price = history['Close'].iloc[-1]
                    prev_price = history['Close'].iloc[-2] if len(history) > 1 else current_price
                    change = current_price - prev_price
                    pct_change = (change / prev_price) * 100
                    
                    color = "green" if change >= 0 else "red"
                    st.metric(label="Current Price", value=f"{current_price:,.2f}", delta=f"{change:.2f} ({pct_change:.2f}%)")
                    
                    # Chart
                    st.line_chart(history['Close'])
                else:
                    st.warning("Price data currently unavailable.")

            # TAB 2: SENTIMENT
            with tabs[1]:
                st.subheader("📰 AI News Sentiment")
                news = stock.news
                if news:
                    results_list = []
                    # Progress bar for UX
                    progress_bar = st.progress(0)
                    
                    for i, article in enumerate(news[:10]):
                        progress_bar.progress((i + 1) / 10)
                        story = article.get('content', {}) 
                        summary = story.get('summary', 'No Summary')
                        title = story.get('title', 'No Title')
                        
                        if summary != 'No Summary':
                            res = pipe(summary)[0]
                            results_list.append({"title": title, "label": res['label'], "score": res['score']})
                    
                    progress_bar.empty()
                    
                    if results_list:
                        pos = sum(1 for r in results_list if r['label'] == 'positive')
                        neg = sum(1 for r in results_list if r['label'] == 'negative')
                        
                        # Mood Badge
                        if pos > neg: mood = "BULLISH 🐂"
                        elif neg > pos: mood = "BEARISH 🐻"
                        else: mood = "NEUTRAL ⚖️"

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Positive Articles", pos)
                        c2.metric("Negative Articles", neg)
                        c3.metric("Market Mood", mood)
                        
                        st.divider()
                        for item in results_list:
                            emoji = "🟢" if item['label'] == 'positive' else "🔴" if item['label'] == 'negative' else "⚪"
                            with st.expander(f"{emoji} {item['label'].upper()}: {item['title']}"):
                                st.write(f"Confidence: {item['score']:.2f}")
                else:
                    st.warning("No news found for this asset.")

            # TAB 3: STATS
            with tabs[2]:
                st.subheader("📋 Fundamental Data")
                st.json(stock.info)

        # ==========================================
        # LOGIC FOR DERIVATIVES (OPTIONS)
        # ==========================================
        else:
            # Check for Expiry Dates
            expirations = stock.options
            
            if expirations:
                # TAB 1: CHAIN
                with tabs[0]:
                    st.subheader(f"Options Chain for {ticker}")
                    selected_expiry = st.selectbox("Select Expiry Date:", expirations)
                    
                    with st.spinner("Fetching Chain..."):
                        chain = stock.option_chain(selected_expiry)
                        calls = chain.calls
                        puts = chain.puts
                        
                        # Filter for Near-the-Money (Optional but cleaner)
                        # For now, just show top 10 most active
                        st.markdown(f"**🔥 Top Active Calls (Bullish Bets)**")
                        st.dataframe(calls.sort_values('openInterest', ascending=False).head(10)[['contractSymbol', 'strike', 'lastPrice', 'percentChange', 'openInterest', 'volume']])
                        
                        st.markdown(f"**🔥 Top Active Puts (Bearish Bets)**")
                        st.dataframe(puts.sort_values('openInterest', ascending=False).head(10)[['contractSymbol', 'strike', 'lastPrice', 'percentChange', 'openInterest', 'volume']])

                # TAB 2: RATIOS
                with tabs[1]:
                    st.subheader("📊 Open Interest Analysis")
                    total_call_oi = calls['openInterest'].sum()
                    total_put_oi = puts['openInterest'].sum()
                    
                    c1, c2 = st.columns(2)
                    c1.metric("Total Call OI", f"{total_call_oi:,}")
                    c2.metric("Total Put OI", f"{total_put_oi:,}")
                    
                    if total_call_oi > 0:
                        pcr = total_put_oi / total_call_oi
                        st.metric("Put-Call Ratio (PCR)", f"{pcr:.2f}")
                        
                        if pcr > 1:
                            st.error(f"PCR is {pcr:.2f} (>1). Bears are dominating. (Bearish Signal)")
                        elif pcr < 0.7:
                            st.success(f"PCR is {pcr:.2f} (<0.7). Bulls are dominating. (Bullish Signal)")
                        else:
                            st.info(f"PCR is {pcr:.2f}. Market is Neutral/Mixed.")
                            
                        # Chart
                        fig = go.Figure(data=[go.Pie(labels=['Calls (Bulls)', 'Puts (Bears)'], values=[total_call_oi, total_put_oi], hole=.4)])
                        st.plotly_chart(fig)

                # TAB 3: RAW
                with tabs[2]:
                    st.write("Full Call Data:")
                    st.dataframe(calls)
                    st.write("Full Put Data:")
                    st.dataframe(puts)

            else:
                st.error(f"No Options Data Found for {ticker}. This usually means the API does not support derivatives for this specific Indian stock. Try selecting 'Apple (US Demo)' or 'Tesla (US Demo)' to see this feature in action.")

    except Exception as e:
        st.error(f"Error: {e}")
