import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from transformers import pipeline

# 1. Page Configuration & Professional UI Styling
st.set_page_config(page_title="Market Analyzer Pro", page_icon="📈", layout="wide")

# CUSTOM CSS: Fixed text visibility for Dark Sidebar
st.markdown("""
    <style>
    /* Main Page Background */
    .main { background-color: #f8f9fa; }
    
    /* Metric Card Styling */
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    
    /* SIDEBAR DARK THEME */
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#1e293b, #0f172a);
        color: white;
    }
    
    /* FIX: Force Input Text to be Dark/Visible */
    [data-testid="stSidebar"] input {
        color: #1e293b !important;
    }
    
    /* FIX: Force Dropdown Text to be Dark/Visible */
    div[data-baseweb="select"] * {
        color: #1e293b !important;
    }
    
    /* Sidebar Labels (White for contrast against dark blue) */
    [data-testid="stSidebar"] label {
        color: white !important;
        font-weight: 600;
    }

    /* Execute Analysis Button Styling */
    div.stButton > button:first-child {
        background-color: #ffffff;
        color: #0f172a;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        height: 3em;
        width: 100%;
    }
    
    div.stButton > button:hover {
        background-color: #e2e8f0;
        color: #0f172a;
    }

    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# DASHBOARD HEADER
st.title("📈 Market Analyzer Pro")
st.caption("Strategic AI-Powered Sentiment & Market Analysis")

# --- Load AI Model (Cached) ---
@st.cache_resource
def load_model():
    return pipeline("text-classification", model="ProsusAI/finbert")

with st.spinner("Initializing AI Engines..."):
    pipe = load_model()

# --- THE MEGA LIST (Expanded & Sorted) ---
INDICES = {
    "Nifty 50": "^NSEI", "Sensex": "^BSESN", "Nifty Bank": "^NSEBANK", "Nifty IT": "^CNXIT", "S&P 500": "^GSPC"
}

STOCKS = {
    "Adani Ent": "ADANIENT.NS", "Asian Paints": "ASIANPAINT.NS", "Axis Bank": "AXISBANK.NS",
    "Bajaj Finance": "BAJFINANCE.NS", "Bharti Airtel": "BHARTIARTL.NS", "Coal India": "COALINDIA.NS",
    "HCL Tech": "HCLTECH.NS", "HDFC Bank": "HDFCBANK.NS", "Hindustan Unilever": "HINDUNILVR.NS",
    "ICICI Bank": "ICICIBANK.NS", "Infosys": "INFY.NS", "ITC": "ITC.NS", "Jio Financial": "JIOFIN.NS",
    "Kotak Bank": "KOTAKBANK.NS", "L&T": "LT.NS", "M&M": "M&M.NS", "Maruti": "MARUTI.NS",
    "NTPC": "NTPC.NS", "Paytm": "PAYTM.NS", "Power Grid": "POWERGRID.NS", "Reliance Industries": "RELIANCE.NS",
    "SBI": "SBIN.NS", "Sun Pharma": "SUNPHARMA.NS", "Suzlon": "SUZLON.NS", "Tata Motors": "TATAMOTORS.NS",
    "Tata Steel": "TATASTEEL.NS", "TCS": "TCS.NS", "Titan": "TITAN.NS", "UltraTech": "ULTRACEMCO.NS",
    "Vedanta": "VEDL.NS", "Wipro": "WIPRO.NS", "Zomato": "ZOMATO.NS",
    "Apple (US Demo)": "AAPL", "Tesla (US Demo)": "TSLA"
}

# --- SIDEBAR: TERMINAL CONTROLS ---
with st.sidebar:
    st.header("🎛️ Terminal Controls")
    
    # 1. Asset Class Selection
    asset_class = st.selectbox("Select Asset Class:", ["Equities (Stocks)", "Indices (Market View)", "Derivatives (Options)"])
    
    st.divider()
    
    # 2. Dynamic Instrument Selection
    st.subheader("Select Instrument")
    current_list = INDICES if asset_class == "Indices (Market View)" else STOCKS
    sorted_keys = sorted(list(current_list.keys()))
    
    dropdown_name = st.selectbox("Choose from list:", sorted_keys)
    dropdown_ticker = current_list[dropdown_name]
    
    # 3. Manual Ticker Override
    manual_ticker = st.text_input("OR Type Any Ticker (e.g. IRFC.NS):", "")
    ticker = manual_ticker.upper() if manual_ticker else dropdown_ticker
    
    # Visual Confirmation of Target
    st.markdown(f"""
        <div style="background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #60a5fa;">
            <span style="font-size: 0.8em; color: #94a3b8;">Targeting:</span><br>
            <strong style="color: white; font-size: 1.1em;">{ticker}</strong>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    num_articles = st.slider("Analysis Depth (Articles):", 5, 50, 15)
    
    analyze_btn = st.button("Execute Analysis ⚡")
    
    # THE SIGNATURE
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🛠️ Built by **Squaddyy**")
    st.caption("Your neighborhood programmer")

# --- MAIN DASHBOARD LOGIC ---
if analyze_btn:
    try:
        stock = yf.Ticker(ticker)
        tabs = st.tabs(["📈 Price Dynamics", "📰 AI Sentiment", "📋 Fundamentals"])

        # TAB 1: PRICE ACTION
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

                st.metric(label=f"{ticker} Current", value=f"₹{current:,.2f}", delta=f"{change:.2f} ({pct_change:.2f}%)")
                
                t1, t2, t3, t4 = st.columns(4)
                try:
                    t1.metric("Open", f"₹{info.get('open', 'N/A')}")
                    t2.metric("High", f"₹{info.get('dayHigh', 'N/A')}")
                    t3.metric("Low", f"₹{info.get('dayLow', 'N/A')}")
                    t4.metric("Close (Prev)", f"₹{prev_close:,.2f}")
                except:
                    st.caption("Technical details temporarily limited by API.")

                fig = go.Figure(data=[go.Candlestick(x=history.index, open=history['Open'], high=history['High'], low=history['Low'], close=history['Close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, height=550, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        # TAB 2: SENTIMENT
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
                    c1.metric("Positive", pos)
                    c2.metric("Negative", neg, delta_color="inverse")
                    c3.metric("Market Mood", "BULLISH 🐂" if pos > neg else "BEARISH 🐻" if neg > pos else "NEUTRAL ⚖️")
                    
                    st.divider()
                    for r in results:
                        emoji = "🟢" if r['label'] == 'positive' else "🔴" if r['label'] == 'negative' else "⚪"
                        with st.expander(f"{emoji} {r['label'].upper()}: {r['title']}"):
                            st.write(f"AI Confidence: {r['score']:.2f}")

        # TAB 3: KEY STATS
        with tabs[2]:
            st.subheader("📋 Fundamental Profile")
            try:
                info = stock.info
                if info and len(info) > 10:
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Market Cap", f"₹{info.get('marketCap', 0):,}")
                    k1.metric("P/E Ratio", info.get('trailingPE', 'N/A'))
                    k2.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 0):,}")
                    k2.metric("52W Low", f"₹{info.get('fiftyTwoWeekLow', 0):,}")
                    k3.metric("Div. Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%")
                    k3.metric("Avg Volume", f"{info.get('averageVolume', 0):,}")
                else:
                    st.warning("Key stats currently on cooldown due to API limits.")
            except:
                st.error("Fundamental data unavailable.")

    except Exception as e:
        st.error(f"Analysis Error: {e}")
