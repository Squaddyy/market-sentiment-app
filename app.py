import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from transformers import pipeline

# 1. Page Configuration & Professional UI Styling
st.set_page_config(page_title="Market Analyzer Pro", page_icon="📈", layout="wide")

# Initialize Session State
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'manual_ticker' not in st.session_state:
    st.session_state.manual_ticker = ""

# CALLBACK: This is the fix for the Favorites buttons
def select_favorite(ticker):
    st.session_state.manual_ticker = ticker
    # We force an analysis run immediately
    st.session_state.run_analysis = True

# CUSTOM CSS: Fixed text visibility and Terminal design
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    [data-testid="stSidebar"] { background-image: linear-gradient(#1e293b, #0f172a); color: white; }
    [data-testid="stSidebar"] input { color: #1e293b !important; }
    div[data-baseweb="select"] * { color: #1e293b !important; }
    [data-testid="stSidebar"] label { color: white !important; font-weight: 600; }
    div.stButton > button:first-child { background-color: #ffffff; color: #0f172a; border-radius: 8px; font-weight: bold; width: 100%; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Market Analyzer Pro")
st.caption("One dashboard for all your finance things")

# --- Load AI Model (Cached) ---
@st.cache_resource
def load_model():
    return pipeline("text-classification", model="ProsusAI/finbert")

with st.spinner("Initializing AI Engines..."):
    pipe = load_model()

# --- THE MEGA LIST ---
INDICES = {"Nifty 50": "^NSEI", "Sensex": "^BSESN", "Nifty Bank": "^NSEBANK", "Nifty IT": "^CNXIT", "S&P 500": "^GSPC"}
STOCKS = {
    "Adani Ent": "ADANIENT.NS", "Asian Paints": "ASIANPAINT.NS", "Axis Bank": "AXISBANK.NS",
    "Bajaj Finance": "BAJFINANCE.NS", "Bharti Airtel": "BHARTIARTL.NS", "Coal India": "COALINDIA.NS",
    "HCL Tech": "HCLTECH.NS", "HDFC Bank": "HDFCBANK.NS", "Hindustan Unilever": "HINDUNILVR.NS",
    "ICICI Bank": "ICICIBANK.NS", "Infosys": "INFY.NS", "ITC": "ITC.NS", "Jio Financial": "JIOFIN.NS",
    "Kotak Bank": "KOTAKBANK.NS", "L&T": "LT.NS", "M&M": "M&M.NS", "Maruti": "MARUTI.NS",
    "NTPC": "NTPC.NS", "Paytm": "PAYTM.NS", "Power Grid": "POWERGRID.NS", "Reliance Industries": "RELIANCE.NS",
    "SBI": "SBIN.NS", "Sun Pharma": "SUNPHARMA.NS", "Suzlon": "SUZLON.NS", "Tata Motors": "TATAMOTORS.NS",
    "Tata Steel": "TATASTEEL.NS", "TCS": "TCS.NS", "Titan": "TITAN.NS", "UltraTech": "ULTRACEMCO.NS",
    "Vedanta": "VEDL.NS", "Wipro": "WIPRO.NS", "Zomato": "ZOMATO.NS"
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
    
    # Text input linked to session state for favorites functionality
    ticker_input = st.text_input("OR Type Any Ticker (e.g. IRFC.NS):", key="manual_ticker")
    
    final_ticker = ticker_input.upper() if ticker_input else dropdown_ticker
    
    st.markdown(f"""
        <div style="background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #60a5fa;">
            <span style="font-size: 0.8em; color: #94a3b8;">Targeting:</span><br>
            <strong style="color: white; font-size: 1.1em;">{final_ticker}</strong>
        </div>
    """, unsafe_allow_html=True)
    
    if st.button("⭐ Add/Remove Favorite"):
        if final_ticker in st.session_state.favorites:
            st.session_state.favorites.remove(final_ticker)
            st.toast(f"Removed {final_ticker}")
        else:
            st.session_state.favorites.append(final_ticker)
            st.toast(f"Added {final_ticker}")

    num_articles = st.slider("Analysis Depth (Articles):", 5, 50, 15)
    analyze_btn = st.button("Execute Analysis ⚡", key="main_analyze_btn")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🛠️ Built by **Squaddyy**")
    st.caption("Your neighborhood programmer")

# --- MAIN DASHBOARD LOGIC ---
# Analysis triggers if button is pressed OR if a favorite was just clicked
if analyze_btn or st.session_state.get('run_analysis'):
    # Reset the flag
    st.session_state.run_analysis = False
    
    try:
        stock = yf.Ticker(final_ticker)
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

                st.metric(label=f"{final_ticker} Current", value=f"₹{current:,.2f}", delta=f"{current - prev_close:.2f}")
                st.caption("*Note: Data may have a 15-min delay (Standard for free APIs).*")
                
                fig = go.Figure(data=[go.Candlestick(x=history.index, open=history['Open'], high=history['High'], low=history['Low'], close=history['Close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, height=550, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

        with tabs[1]:
            news = stock.news
            if news:
                results = []
                for art in news[:num_articles]:
                    story = art.get('content', {})
                    if story.get('summary'):
                        res = pipe(story['summary'])[0]
                        results.append({"title": story['title'], "label": res['label']})
                
                if results:
                    pos = sum(1 for r in results if r['label'] == 'positive')
                    neg = sum(1 for r in results if r['label'] == 'negative')
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Positive", pos)
                    c2.metric("Negative", neg, delta_color="inverse")
                    c3.metric("Mood", "BULLISH 🐂" if pos > neg else "BEARISH 🐻")
                    for r in results:
                        st.write(f"- {r['title']}")

        with tabs[2]:
            st.subheader("📋 Fundamentals")
            try:
                info = stock.info
                k1, k2, k3 = st.columns(3)
                k1.metric("Market Cap", f"₹{info.get('marketCap', 0):,}")
                k2.metric("P/E Ratio", info.get('trailingPE', 'N/A'))
                k3.metric("52W High", f"₹{info.get('fiftyTwoWeekHigh', 0):,}")
                
                # Ownership Pie
                inst = info.get('heldPercentInstitutions', 0) * 100
                insider = info.get('heldPercentInsiders', 0) * 100
                fig_own = go.Figure(data=[go.Pie(labels=['Inst', 'Insider', 'Retail'], values=[inst, insider, 100-inst-insider], hole=.3)])
                st.plotly_chart(fig_own, use_container_width=True)
            except:
                st.error("Fundamental data unavailable.")

    except Exception as e:
        st.error(f"Analysis Error: {e}")
else:
    # --- WELCOME SCREEN WITH FIXED HEATMAP & CLICKABLE FAVORITES ---
    st.subheader(f"👋 Welcome to your terminal!")
    
    col_fav, col_heat = st.columns([1, 2])
    
    with col_fav:
        st.markdown("### ⭐ Your Favorites")
        if st.session_state.favorites:
            for fav in st.session_state.favorites:
                # Callback fix: clicking this button now reloads the app with this ticker
                st.button(f"🔍 Analyze {fav}", key=f"fav_{fav}", on_click=select_favorite, args=(fav,))
        else:
            st.write("No favorites yet. Add some in the sidebar!")

    with col_heat:
        st.markdown("### 🗺️ Live Sector Performance (Nifty)")
        sectors = {"Nifty Bank": "^NSEBANK", "Nifty IT": "^CNXIT", "Nifty Auto": "NIFTY_AUTO.NS", "Nifty Pharma": "NIFTY_PHARMA.NS"}
        
        heat_results = []
        for name, tick in sectors.items():
            try:
                s_data = yf.Ticker(tick).history(period="1d")
                change = ((s_data['Close'].iloc[-1] - s_data['Open'].iloc[0]) / s_data['Open'].iloc[0]) * 100
                heat_results.append({"Sector": name, "Performance": change, "Group": "Market"})
            except: continue
                
        if heat_results:
            df_heat = pd.DataFrame(heat_results)
            # Fix: Added 'maxdepth=1' to prevent the blank screen drill-down
            fig_heat = px.treemap(df_heat, path=['Group', 'Sector'], values=[1]*len(df_heat),
                                 color='Performance', color_continuous_scale='RdYlGn',
                                 color_continuous_midpoint=0, range_color=[-3, 3])
            fig_heat.update_layout(margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig_heat, use_container_width=True)

    st.info("Ready? Select an instrument or click a favorite and hit **Execute Analysis**.")
