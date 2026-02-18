import streamlit as st
import yfinance as yf
from transformers import pipeline

# 1. Setup the page layout
st.set_page_config(page_title="Market Sentiment", page_icon="📈", layout="wide")
st.title("📈 Market Sentiment Dashboard")

# --- Load the AI Model ---
@st.cache_resource
def load_model():
    return pipeline("text-classification", model="ProsusAI/finbert")

with st.spinner("Loading AI Brain..."):
    pipe = load_model()

# 2. Sidebar / User Input
with st.sidebar:
    st.header("⚙️ Settings")
    
    # --- EXPANDED LIST: Nifty 50 & Popular Stocks ---
    popular_stocks = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "LICI.NS",
        "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "KOTAKBANK.NS", "AXISBANK.NS",
        "ASIANPAINT.NS", "TITAN.NS", "MARUTI.NS", "SUNPHARMA.NS", "ULTRACEMCO.NS",
        "TATAMOTORS.NS", "NTPC.NS", "POWERGRID.NS", "ADANIENT.NS", "ONGC.NS",
        "WIPRO.NS", "M&M.NS", "JSWSTEEL.NS", "COALINDIA.NS", "TATASTEEL.NS",
        "PIDILITIND.NS", "BRITANNIA.NS", "TECHM.NS", "SIEMENS.NS", "INDIGO.NS",
        "ZOMATO.NS", "PAYTM.NS", "NAUKRI.NS", "POLICYBZR.NS", "DLF.NS"
    ]
    # Sort alphabetically for easier finding
    popular_stocks.sort()
    
    st.subheader("1. Quick Select")
    dropdown_ticker = st.selectbox("Choose a stock:", popular_stocks)
    
    st.subheader("2. Or Search Any Stock")
    custom_ticker = st.text_input("Enter Ticker (e.g. VEDL.NS):", "")
    
    # Logic: Custom input overrides dropdown
    if custom_ticker:
        ticker = custom_ticker.upper()
    else:
        ticker = dropdown_ticker
        
    st.info(f"Analyzing: **{ticker}**")
    
    # --- NEW: Slider for number of articles ---
    # Letting YOU choose speed vs. depth
    num_articles = st.slider("Number of Articles to Analyze:", min_value=5, max_value=50, value=15)
    
    analyze_btn = st.button("Run Analysis 🚀")

# 3. Main Dashboard
if analyze_btn:
    # --- SECTION 1: PRICE & TECHNICALS ---
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # --- IMPROVED PRICE FETCHING ---
        # We try 'currentPrice' first (most accurate live), then 'regularMarketPrice'
        current = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
        previous = info.get('previousClose') or info.get('regularMarketPreviousClose')
        open_price = info.get('open') or info.get('regularMarketOpen')
        day_high = info.get('dayHigh') or info.get('regularMarketDayHigh')
        day_low = info.get('dayLow') or info.get('regularMarketDayLow')
        
        # Calculate Change
        if current and previous:
            change = current - previous
            change_pct = (change / previous) * 100
        else:
            change = 0
            change_pct = 0

        # Main Price Display
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric(
                label=f"{ticker} Price",
                value=f"₹{current:,.2f}" if current else "N/A",
                delta=f"{change:.2f} ({change_pct:.2f}%)" if current else None
            )
            # Disclaimer
            st.caption("*Note: Data may have a 15-min delay (Standard for free APIs).*")
        
        # Extra Data Grid
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Open", f"₹{open_price:,.2f}" if open_price else "-")
        m2.metric("Day High", f"₹{day_high:,.2f}" if day_high else "-")
        m3.metric("Day Low", f"₹{day_low:,.2f}" if day_low else "-")
        m4.metric("Prev. Close", f"₹{previous:,.2f}" if previous else "-")
        
        st.divider()

        # --- SECTION 2: CHART ---
        st.subheader("📉 Price Trend (1 Month)")
        history = stock.history(period="1mo")
        st.line_chart(history['Close'])
        st.divider()

        # --- SECTION 3: AI NEWS ANALYSIS ---
        st.subheader(f"📰 AI Sentiment Analysis (Last {num_articles} Articles)")
        
        # Progress Bar for the heavier workload
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            news = stock.news
            if news:
                results_list = []
                # Use the slider value to limit articles
                articles_to_check = news[:num_articles]
                
                for i, article in enumerate(articles_to_check):
                    # Update progress bar
                    progress = (i + 1) / len(articles_to_check)
                    progress_bar.progress(progress)
                    
                    story = article.get('content', {}) 
                    summary = story.get('summary', 'No Summary Available')
                    title = story.get('title', 'No Title Available')
                    
                    if summary and summary != 'No Summary Available':
                        result = pipe(summary)[0]
                        results_list.append({
                            "title": title,
                            "summary": summary,
                            "label": result['label'],
                            "score": result['score']
                        })
                
                # Clear progress bar
                progress_bar.empty()
                
                # Dashboard Logic
                if results_list:
                    pos = sum(1 for r in results_list if r['label'] == 'positive')
                    neg = sum(1 for r in results_list if r['label'] == 'negative')
                    
                    if pos > neg:
                        mood = "BULLISH 🐂"
                    elif neg > pos:
                        mood = "BEARISH 🐻"
                    else:
                        mood = "NEUTRAL ⚖️"
                    
                    # Sentiment Metrics
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Articles Read", len(results_list))
                    k2.metric("Positive", pos)
                    k3.metric("Negative", neg)
                    k4.metric("Market Mood", mood)
                    
                    st.divider()
                    
                    # Display Articles
                    for item in results_list:
                        emoji = "🟢" if item['label'] == 'positive' else "🔴" if item['label'] == 'negative' else "⚪"
                        with st.expander(f"{emoji} {item['label'].upper()}: {item['title']}"):
                            st.write(item['summary'])
                            st.caption(f"Confidence: {item['score']:.2f}")

            else:
                st.warning("No news articles found for this stock.")
                
        except Exception as e:
            st.error(f"Error analyzing news: {e}")
                
    except Exception as e:
        st.error(f"Error: {e}")