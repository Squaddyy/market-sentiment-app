import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from transformers import pipeline

# 1. Page Configuration & Professional UI Styling
st.set_page_config(page_title="Market Analyzer Pro", page_icon="📈", layout="wide")

# Initialize Favorites in Session State if not exists
if 'favorites' not in st.session_state:
    st.session_state.favorites = []

# CUSTOM CSS: Premium Terminal aesthetic and text visibility
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#1e293b, #0f172a);
        color: white;
    }
    [data-testid="stSidebar"] input { color: #1e293b !important; }
    div[data-baseweb="select"] * { color: #1e293b !important; }
    [data-testid="stSidebar"] label { color: white !important; font-weight: 600; }

    div.stButton > button:first-child {
        background-color: #ffffff;
        color: #0f172a;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        height: 3em;
        width: 100%;
    }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# DASHBOARD HEADER
st.title("📈 Market Analyzer Pro")
st.caption("One dashboard for all your finance things")

# --- Load AI Model (Cached) ---
@st.cache_resource
def load_model():
    return pipeline("text-classification", model="ProsusAI/finbert")

with st.spinner("Initializing AI Engines..."):
    pipe = load_model()

# --- THE MEGA LIST ---
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
    asset_class = st.selectbox("Select Asset Class:", ["Equities (Stocks)", "Indices (Market View)", "Derivatives (Options)"])
    st.divider()
    
    st.subheader("Select Instrument")
    current_list = INDICES if asset_class == "Indices (Market View)" else STOCKS
    sorted_keys = sorted(list(current_list.keys()))
    dropdown_name = st.selectbox("Choose from list:", sorted_keys)
    dropdown_ticker = current_list[dropdown_name]
    
    manual_ticker = st.text_input("OR Type Any Ticker (e.g. IRFC.NS):", "")
    ticker = manual_ticker.upper() if manual_ticker else dropdown_ticker
    
    st.markdown(f"""
        <div style="background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #60a5fa;">
            <span style="font-size: 0.8em; color: #94a3b8;">Targeting:</span><br>
            <strong style="color: white; font-size: 1.1em;">{ticker}</strong>
        </div>
    """, unsafe_allow_html=True)
    
    # FAVORITES TOGGLE
    if st.button("⭐ Add/Remove Favorite"):
        if ticker in st.session_state.favorites:
            st.session_state.favorites.remove(ticker)
            st.toast(f"Removed {ticker} from favorites")
        else:
            st.session_state.favorites.append(ticker)
            st.toast(f"Added {ticker} to favorites")

    st.write("")
    num_articles = st.slider("Analysis Depth (Articles):", 5, 50, 15)
    analyze_btn = st.button("Execute Analysis ⚡")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🛠️ Built by **Squaddyy**")
    st.caption("Your neighborhood programmer")

# --- MAIN DASHBOARD LOGIC ---
if analyze_btn:
    try:
        stock = yf.Ticker(ticker)
        tabs = st.tabs(["📈 Price Dynamics", "📰 AI Sentiment", "📋 Fundamentals & Peers"])

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
                st.caption("*Note: Data may have a 15-min delay (Standard for free APIs).*")
                
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
                    
                    st.divider()
                    st.subheader("🏦 Ownership & Peers")
                    p1, p2 = st.columns(2)
                    with p1:
                        inst_own = info.get('heldPercentInstitutions', 0) * 100
                        insider_own = info.get('heldPercentInsiders', 0) * 100
                        fig_own = go.Figure(data=[go.Pie(labels=['Institutions', 'Insiders', 'Retail/Other'], 
                                                        values=[inst_own, insider_own, 100 - inst_own - insider_own],
                                                        hole=.3)])
                        fig_own.update_layout(title="Shareholding Pattern")
                        st.plotly_chart(fig_own, use_container_width=True)
                    with p2:
                        st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                        st.write(f"**Industry:** {info.get('industry', 'N/A')}")
                        st.info("💡 Compare this P/E with industry averages to find valuation gaps.")
                else:
                    st.warning("Key stats currently on cooldown due to API limits.")
            except:
                st.error("Fundamental data unavailable.")

    except Exception as e:
        st.error(f"Analysis Error: {e}")
else:
    # --- UPDATED WELCOME SCREEN WITH HEATMAP & FAVORITES ---
    st.subheader(f"👋 Welcome to your terminal!")
    
    col_fav, col_heat = st.columns([1, 2])
    
    with col_fav:
        st.markdown("### ⭐ Your Favorites")
        if st.session_state.favorites:
            for fav in st.session_state.favorites:
                st.button(f"🔍 Analyze {fav}", key=fav, on_click=lambda f=fav: st.write(f"Selected {f} (Hit Analysis button below)"))
        else:
            st.write("No favorites yet. Add some in the sidebar!")

    with col_heat:
        st.markdown("### 🗺️ Sector Heatmap (Sample)")
        # Sample Heatmap Data
        heatmap_data = pd.DataFrame({
            "Sector": ["Banking", "IT", "Energy", "Consumer", "Auto", "Pharma"],
            "Performance": [1.2, -0.8, 2.5, 0.4, -1.5, 0.9],
            "Parent": ["Market", "Market", "Market", "Market", "Market", "Market"]
        })
        fig_heat = px.treemap(heatmap_data, path=['Parent', 'Sector'], values=[1,1,1,1,1,1],
                             color='Performance', color_continuous_scale='RdYlGn',
                             range_color=[-3, 3])
        st.plotly_chart(fig_heat, use_container_width=True)

    st.info("Ready to analyze? Select an instrument from the sidebar and hit **Execute Analysis**.")
