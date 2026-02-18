import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from transformers import pipeline

# 1. Page Configuration
st.set_page_config(page_title="Market Analyzer Pro", page_icon="📈", layout="wide")

# --- Persistent Session State ---
if 'favorites' not in st.session_state: st.session_state.favorites = []
if 'manual_ticker' not in st.session_state: st.session_state.manual_ticker = ""
if 'run_analysis' not in st.session_state: st.session_state.run_analysis = False

def select_favorite(ticker):
    st.session_state.manual_ticker = ticker
    st.session_state.run_analysis = True

# --- Currency Formatter ---
def format_currency(value):
    if not isinstance(value, (int, float)): return value
    if value >= 1e12: return f"₹{value/1e12:.2f}T"
    elif value >= 1e9: return f"₹{value/1e9:.2f}B"
    elif value >= 1e7: return f"₹{value/1e7:.2f}Cr"
    elif value >= 1e5: return f"₹{value/1e5:.2f}L"
    else: return f"₹{value:,.2f}"

# --- CUSTOM CSS: THE "NUCLEAR" VISIBILITY FIX ---
st.markdown("""
    <style>
    /* 1. Main Background */
    .main {
        background-color: #f1f5f9;
        background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
        background-size: 30px 30px;
    }
    
    /* 2. Sidebar Container - Dark Blue Gradient */
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#1e293b, #0f172a);
        border-right: 1px solid #334155;
    }

    /* 3. SIDEBAR TEXT: Force Bright White */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
    }

    /* 4. INPUT BOXES: White Box, Dark Text */
    [data-testid="stSidebar"] input {
        color: #0f172a !important;
        background-color: #ffffff !important;
    }
    /* Fix Dropdown Menu */
    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    div[data-baseweb="select"] span {
        color: #0f172a !important; 
    }
    /* Fix the text inside the dropdown list when clicked */
    ul[data-testid="stSelectboxVirtualDropdown"] li span {
        color: #0f172a !important;
    }

    /* 5. BUTTON STYLING (The Fix for Favorites) */
    /* Forces button text to be Dark Blue so it's visible on White button */
    div.stButton > button {
        background-color: #ffffff !important;
        color: #0f172a !important; /* This makes the text visible */
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        border-color: #3b82f6 !important;
        color: #3b82f6 !important;
    }
    
    /* 6. Metric Cards */
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); 
        border: 1px solid #e2e8f0;
    }
    
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Market Analyzer Pro")
st.caption("One dashboard for all your finance things")

# --- AI Engine ---
@st.cache_resource
def load_model():
    return pipeline("text-classification", model="ProsusAI/finbert")

with st.spinner("Initializing AI Engines..."):
    pipe = load_model()

# --- Lists ---
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

# --- Sidebar ---
with st.sidebar:
    st.header("🎛️ Terminal Controls")
    asset_class = st.selectbox("Select Asset Class:", ["Equities (Stocks)", "Indices (Market View)", "Derivatives (Options)"])
    st.divider()
    
    current_list = INDICES if asset_class == "Indices (Market View)" else STOCKS
    dropdown_name = st.selectbox("Choose from list:", sorted(list(current_list.keys())))
    
    ticker_input = st.text_input("OR Type Any Ticker (e.g. IRFC.NS):", key="manual_ticker_input")
    final_ticker = ticker_input.upper() if ticker_input else current_list[dropdown_name]
    
    st.markdown(f"""<div style="background-color: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #60a5fa;">
        <strong style="color: white; font-size: 1.1em;">{final_ticker}</strong></div>""", unsafe_allow_html=True)
    
    if st.button("⭐ Add/Remove Favorite"):
        if final_ticker in st.session_state.favorites:
            st.session_state.favorites.remove(final_ticker)
            st.toast(f"Removed {final_ticker}")
        else:
            st.session_state.favorites.append(final_ticker)
            st.toast(f"Added {final_ticker}")

    num_articles = st.slider("Analysis Depth (Articles):", 5, 50, 15)
    analyze_btn = st.button("Execute Analysis ⚡")
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🛠️ Built by **Squaddyy**")
    st.caption("Your neighborhood programmer")

# --- Main Logic ---
if analyze_btn or st.session_state.run_analysis:
    st.session_state.run_analysis = False
    
    try:
        stock = yf.Ticker(final_ticker)
        history = stock.history(period="6mo")
        
        if not history.empty:
            tabs = st.tabs(["📈 Price Dynamics", "📰 AI Sentiment", "📋 Fundamentals & Peers"])

            with tabs[0]:
                current = history['Close'].iloc[-1]
                prev_close = history['Close'].iloc[-2]
                change = current - prev_close
                pct_change = (change / prev_close) * 100
                
                st.metric(label=f"{final_ticker} Current", value=f"₹{current:,.2f}", delta=f"{change:.2f} ({pct_change:.2f}%)")
                st.caption("*Note: Data may have a 15-min delay.*")
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Open", f"₹{history['Open'].iloc[-1]:,.2f}")
                c2.metric("High", f"₹{history['High'].iloc[-1]:,.2f}")
                c3.metric("Low", f"₹{history['Low'].iloc[-1]:,.2f}")
                c4.metric("Prev. Close", f"₹{prev_close:,.2f}")

                fig = go.Figure(data=[go.Candlestick(x=history.index, open=history['Open'], high=history['High'], low=history['Low'], close=history['Close'])])
                fig.update_layout(xaxis_rangeslider_visible=False, height=550, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)

            with tabs[1]:
                try:
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
                            c3.metric("Market Mood", "BULLISH 🐂" if pos > neg else "BEARISH 🐻")
                            st.divider()
                            for r in results:
                                emoji = "🟢" if r['label'] == 'positive' else "🔴" if r['label'] == 'negative' else "⚪"
                                with st.expander(f"{emoji} {r['label'].upper()}: {r['title']}"):
                                    st.write(f"**AI Confidence Score:** {r['score']:.2f}")
                    else: st.info("No recent news found.")
                except: st.warning("News unavailable.")

            with tabs[2]:
                st.subheader("📋 Fundamental Profile")
                try:
                    info = stock.info
                    if info:
                        k1, k2, k3 = st.columns(3)
                        k1.metric("Market Cap", format_currency(info.get('marketCap', 0)))
                        k1.metric("P/E Ratio", f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A")
                        k2.metric("52W High", format_currency(info.get('fiftyTwoWeekHigh', 0)))
                        k2.metric("52W Low", format_currency(info.get('fiftyTwoWeekLow', 0)))
                        k3.metric("Div. Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "0%")
                        k3.metric("Avg Volume", format_currency(info.get('averageVolume', 0)))
                        
                        st.divider()
                        st.subheader("🏦 Ownership & Peers")
                        p1, p2 = st.columns(2)
                        with p1:
                            inst = info.get('heldPercentInstitutions', 0) * 100
                            insider = info.get('heldPercentInsiders', 0) * 100
                            fig_own = go.Figure(data=[go.Pie(labels=['Inst', 'Insider', 'Retail'], values=[inst, insider, 100-inst-insider], hole=.3)])
                            fig_own.update_layout(title="Shareholding Pattern")
                            st.plotly_chart(fig_own, use_container_width=True)
                        with p2:
                            st.write(f"**Sector:** {info.get('sector', 'N/A')}")
                            st.write(f"**Industry:** {info.get('industry', 'N/A')}")
                            st.info("💡 Compare this P/E with industry averages to find valuation gaps.")
                    else: st.error("Fundamental data not found.")
                except Exception as e:
                    st.error("⚠️ Fundamentals unavailable (Rate Limit or Data Missing).")
                    if st.button("Retry Fetch 🔄"): st.rerun()

        else: st.error("No price data found. Check ticker symbol.")
    except Exception as e: st.error(f"Critical Error: {e}")

else:
    # --- WELCOME SCREEN ---
    st.subheader(f"👋 Welcome to your terminal!")
    col_fav, col_heat = st.columns([1, 2])
    
    with col_fav:
        st.markdown("### ⭐ Your Favorites")
        if st.session_state.favorites:
            for fav in st.session_state.favorites:
                st.button(f"🔍 Analyze {fav}", key=f"fav_{fav}", on_click=select_favorite, args=(fav,))
        else: st.write("Add favorites in the sidebar!")

    with col_heat:
        st.markdown("### 🗺️ Live Market Map")
        sector_map = {
            "Nifty Bank": ["HDFCBANK.NS", "SBIN.NS", "ICICIBANK.NS"],
            "Nifty IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS"],
            "Nifty Auto": ["TATAMOTORS.NS", "MARUTI.NS", "BAJAJ-AUTO.NS"],
            "Nifty Energy": ["RELIANCE.NS", "NTPC.NS", "ONGC.NS"]
        }
        heat_results = []
        for sector, stocks in sector_map.items():
            try:
                heat_results.append({"Label": sector, "Parent": "Market", "Performance": 0, "Size": 0})
                for s in stocks:
                    s_data = yf.Ticker(s).history(period="1d")
                    if not s_data.empty:
                        change = ((s_data['Close'].iloc[-1] - s_data['Open'].iloc[0]) / s_data['Open'].iloc[0]) * 100
                        heat_results.append({"Label": s.replace(".NS", ""), "Parent": sector, "Performance": change, "Size": abs(change) + 0.1})
            except: continue
        
        if heat_results:
            df_heat = pd.DataFrame(heat_results)
            fig_heat = px.treemap(df_heat, path=['Parent', 'Label'], values='Size', color='Performance', 
                                 color_continuous_scale='RdYlGn', color_continuous_midpoint=0, range_color=[-3, 3],
                                 custom_data=['Performance'])
            fig_heat.update_traces(texttemplate="<b>%{label}</b><br>%{customdata[0]:.2f}%")
            fig_heat.update_layout(margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig_heat, use_container_width=True)
