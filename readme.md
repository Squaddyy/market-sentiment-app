# 📈 Market Analyzer Pro

**One dashboard for all your finance things.** *Built by Squaddyy - Your neighborhood programmer*

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)]([YOUR_APP_LINK_HERE](https://squadystock.streamlit.app/))

![Market Analyzer Pro Demo](demo.png)

## 🚀 Overview
Market Analyzer Pro is a sophisticated financial terminal built with Python. It bridges the gap between raw market data and actionable insights by combining real-time stock tracking, technical analysis, and AI-powered news sentiment into a single, "Anti-Fragile" interface.

## ✨ Key Features
* **Live Market Map:** An interactive Treemap visualizing Nifty sector performance with drill-down capabilities.
* **Hybrid Data Engine:** Smart-switching between "Pro" (Rich Data) and "Lite" (API-Safe) modes to prevent crashes during high traffic.
* **AI Sentiment Analysis:** Uses `ProsusAI/finbert` to analyze news headlines and generate a Bullish/Bearish confidence score.
* **Technical Suite:** Real-time Candlestick charts with Open, High, Low, and Close metrics.
* **Fundamental Profile:** detailed breakdown of Market Cap, P/E Ratios, Ownership patterns, and Peer comparison.
* **Watchlist System:** Persistent "Favorites" list to track your top picks across sessions.

## 🛠️ Tech Stack
* **Frontend:** Streamlit (Custom CSS for "Dark Mode" terminal aesthetic)
* **Data:** yFinance (Real-time NSE/BSE data)
* **Visualization:** Plotly Express & Graph Objects
* **AI/ML:** HuggingFace Transformers (BERT)

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/Squaddyy/market-analyzer-pro.git](https://github.com/Squaddyy/market-analyzer-pro.git)
