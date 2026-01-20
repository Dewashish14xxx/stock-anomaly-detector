"""
Stock Anomaly Detector - Streamlit Dashboard
Real-time visualization of stock prices, anomalies, and forecasts
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config
from src.data.fetcher import StockFetcher
from src.data.storage import DataStorage
from src.analytics.indicators import TechnicalIndicatorCalculator
from src.analytics.detector import AnomalyDetector
from src.analytics.forecaster import StockForecaster

# Page configuration
st.set_page_config(
    page_title="Stock Anomaly Detector",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .anomaly-critical {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        padding: 0.5rem 1rem;
        border-radius: 5px;
        color: white;
        margin: 0.25rem 0;
    }
    .anomaly-warning {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
        padding: 0.5rem 1rem;
        border-radius: 5px;
        color: #333;
        margin: 0.25rem 0;
    }
    .anomaly-info {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 0.5rem 1rem;
        border-radius: 5px;
        color: white;
        margin: 0.25rem 0;
    }
    .stMetric {
        background: rgba(28, 131, 225, 0.1);
        padding: 1rem;
        border-radius: 10px;
    }
    .live-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #00ff00;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 1s infinite;
    }
    .market-closed {
        background-color: #ff4444;
        animation: none;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .live-price {
        font-size: 2rem;
        font-weight: bold;
        color: #00ff00;
    }
    .price-up { color: #26a69a; }
    .price-down { color: #ef5350; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_fetcher():
    return StockFetcher()


@st.cache_resource
def get_detector():
    return AnomalyDetector()


@st.cache_resource
def get_indicator_calculator():
    return TechnicalIndicatorCalculator()


def fetch_stock_data_realtime(ticker: str, period: str = "1mo", cache_ttl: int = 10):
    """Fetch stock data with configurable cache TTL for real-time updates"""
    # Use session state to track last fetch time
    cache_key = f"stock_data_{ticker}_{period}"
    time_key = f"last_fetch_{ticker}"
    
    current_time = time.time()
    
    if cache_key in st.session_state and time_key in st.session_state:
        if current_time - st.session_state[time_key] < cache_ttl:
            return st.session_state[cache_key]
    
    fetcher = get_fetcher()
    df = fetcher.fetch_historical(ticker, period=period)
    
    st.session_state[cache_key] = df
    st.session_state[time_key] = current_time
    
    return df


def get_live_price(ticker: str):
    """Get the current live price for a ticker"""
    fetcher = get_fetcher()
    return fetcher.get_current_price(ticker)


def is_market_open():
    """Check if US stock market is currently open"""
    now = datetime.utcnow()
    # Market hours: 9:30 AM - 4:00 PM ET (14:30 - 21:00 UTC)
    market_open = now.replace(hour=14, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=21, minute=0, second=0, microsecond=0)
    
    # Check if weekday (0=Monday, 6=Sunday)
    is_weekday = now.weekday() < 5
    is_during_hours = market_open <= now <= market_close
    
    return is_weekday and is_during_hours


# Comprehensive stock dictionary with categories
STOCK_CATEGORIES = {
    "🇺🇸 US Tech": {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "GOOGL": "Google",
        "NVDA": "Nvidia",
        "TSLA": "Tesla",
        "META": "Meta",
        "AMZN": "Amazon",
        "NFLX": "Netflix",
        "AMD": "AMD",
    },
    "🇮🇳 Indian Stocks": {
        "RELIANCE.NS": "Reliance",
        "TCS.NS": "TCS",
        "INFY.NS": "Infosys",
        "TATAMOTORS.NS": "Tata Motors",
        "HDFCBANK.NS": "HDFC Bank",
        "ICICIBANK.NS": "ICICI Bank",
        "WIPRO.NS": "Wipro",
        "ITC.NS": "ITC",
        "SBIN.NS": "SBI",
    },
    "🥇 Commodities": {
        "GC=F": "Gold",
        "SI=F": "Silver",
        "CL=F": "Crude Oil",
        "GLD": "Gold ETF",
        "SLV": "Silver ETF",
    },
    "📊 Indices": {
        "^NSEI": "Nifty 50",
        "^BSESN": "BSE Sensex",
        "^GSPC": "S&P 500",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ",
    },
}

# Flatten all stocks for quick lookup
ALL_STOCKS = {}
for category, stocks in STOCK_CATEGORIES.items():
    for ticker, name in stocks.items():
        ALL_STOCKS[ticker] = f"{name} ({ticker})"


def create_price_chart(df: pd.DataFrame, ticker: str, anomalies: list = None):
    """Create interactive candlestick chart with Bollinger Bands"""
    indicator_calc = get_indicator_calculator()
    
    # Calculate indicators
    upper, middle, lower = indicator_calc.calculate_bollinger_bands(df)
    
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f'{ticker} Price & Bollinger Bands', 'RSI', 'MACD')
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # Bollinger Bands
    fig.add_trace(
        go.Scatter(x=df.index, y=upper, name='BB Upper', 
                   line=dict(color='rgba(173, 204, 255, 0.7)', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=middle, name='BB Middle',
                   line=dict(color='rgba(100, 149, 237, 0.7)', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=lower, name='BB Lower',
                   line=dict(color='rgba(173, 204, 255, 0.7)', width=1),
                   fill='tonexty', fillcolor='rgba(173, 204, 255, 0.2)'),
        row=1, col=1
    )
    
    # Mark anomalies on chart
    if anomalies:
        anomaly_times = [a.timestamp for a in anomalies]
        anomaly_prices = [a.current_price for a in anomalies]
        anomaly_types = [a.anomaly_type.value for a in anomalies]
        
        fig.add_trace(
            go.Scatter(
                x=anomaly_times,
                y=anomaly_prices,
                mode='markers',
                name='Anomalies',
                marker=dict(
                    size=15,
                    color='red',
                    symbol='triangle-up',
                    line=dict(color='white', width=2)
                ),
                text=anomaly_types,
                hoverinfo='text+x+y'
            ),
            row=1, col=1
        )
    
    # RSI
    rsi = indicator_calc.calculate_rsi(df)
    fig.add_trace(
        go.Scatter(x=df.index, y=rsi, name='RSI',
                   line=dict(color='#9c27b0', width=2)),
        row=2, col=1
    )
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # MACD
    macd, signal, hist = indicator_calc.calculate_macd(df)
    fig.add_trace(
        go.Scatter(x=df.index, y=macd, name='MACD',
                   line=dict(color='#2196f3', width=2)),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=signal, name='Signal',
                   line=dict(color='#ff9800', width=2)),
        row=3, col=1
    )
    fig.add_trace(
        go.Bar(x=df.index, y=hist, name='Histogram',
               marker_color=np.where(hist >= 0, '#26a69a', '#ef5350')),
        row=3, col=1
    )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_rangeslider_visible=False,
        template='plotly_dark'
    )
    
    return fig


def create_forecast_chart(df: pd.DataFrame, ticker: str):
    """Create Prophet forecast visualization"""
    forecaster = StockForecaster()
    
    if not forecaster.train(ticker, df, 'Close'):
        return None
    
    forecast_df = forecaster.forecast(ticker, periods=30, freq='D')
    
    if forecast_df is None:
        return None
    
    fig = go.Figure()
    
    # Historical prices
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Close'],
            name='Historical',
            line=dict(color='#2196f3', width=2)
        )
    )
    
    # Forecast
    fig.add_trace(
        go.Scatter(
            x=forecast_df['timestamp'],
            y=forecast_df['predicted'],
            name='Forecast',
            line=dict(color='#4caf50', width=2, dash='dash')
        )
    )
    
    # Confidence interval
    fig.add_trace(
        go.Scatter(
            x=pd.concat([forecast_df['timestamp'], forecast_df['timestamp'][::-1]]),
            y=pd.concat([forecast_df['upper_bound'], forecast_df['lower_bound'][::-1]]),
            fill='toself',
            fillcolor='rgba(76, 175, 80, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% Confidence'
        )
    )
    
    fig.update_layout(
        title=f'{ticker} Price Forecast (30 Days)',
        height=400,
        template='plotly_dark',
        showlegend=True
    )
    
    return fig


def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown('<div class="main-header">📈 Stock Anomaly Detector</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Category filter
        category_filter = st.selectbox(
            "📁 Category",
            options=["All"] + list(STOCK_CATEGORIES.keys()),
            index=0
        )
        
        # Filter stocks by category
        if category_filter == "All":
            available_stocks = ALL_STOCKS
        else:
            available_stocks = {
                t: f"{n} ({t})" 
                for t, n in STOCK_CATEGORIES[category_filter].items()
            }
        
        # Stock selection with friendly names
        selected_ticker = st.selectbox(
            "📈 Select Stock",
            options=list(available_stocks.keys()),
            format_func=lambda x: available_stocks.get(x, x),
            index=0
        )
        
        # Time period
        period = st.selectbox(
            "Time Period",
            options=["1d", "5d", "1mo", "3mo", "6mo", "1y"],
            index=2
        )
        
        # Detection thresholds
        st.subheader("Detection Thresholds")
        zscore_threshold = st.slider("Z-Score Threshold", 1.0, 5.0, 3.0, 0.5)
        
        st.markdown("---")
        
        # Real-time settings
        st.subheader("🔴 Real-Time Updates")
        auto_refresh = st.toggle("Enable Auto-Refresh", value=False)
        refresh_interval = st.slider(
            "Refresh Interval (seconds)", 
            min_value=5, 
            max_value=60, 
            value=10,
            disabled=not auto_refresh
        )
        
        # Refresh button
        if st.button("🔄 Refresh Now", use_container_width=True):
            # Clear session state cache
            for key in list(st.session_state.keys()):
                if key.startswith("stock_data_") or key.startswith("last_fetch_"):
                    del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Created with ❤️ using Streamlit**")
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(0.1)  # Small delay to prevent rapid reruns
        st.rerun()
    
    # Market status indicator
    market_open = is_market_open()
    market_status = "🟢 Market Open" if market_open else "🔴 Market Closed"
    indicator_class = "live-indicator" if market_open else "live-indicator market-closed"
    
    # Live price header
    live_price = get_live_price(selected_ticker)
    
    col_status, col_live = st.columns([1, 2])
    with col_status:
        st.markdown(f'<span class="{indicator_class}"></span> {market_status}', unsafe_allow_html=True)
        if auto_refresh:
            st.caption(f"🔄 Auto-refreshing every {refresh_interval}s")
    
    with col_live:
        if live_price:
            st.markdown(f'**{selected_ticker}** Live: <span class="live-price">${live_price:.2f}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Fetch data with configurable cache for real-time
    cache_ttl = refresh_interval if auto_refresh else 300
    with st.spinner(f"Fetching {selected_ticker} data..."):
        df = fetch_stock_data_realtime(selected_ticker, period, cache_ttl)
    
    if df.empty:
        st.error(f"No data available for {selected_ticker}")
        return
    
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
    price_change = current_price - prev_price
    price_change_pct = (price_change / prev_price) * 100
    
    with col1:
        st.metric(
            label=f"💰 {selected_ticker} Price",
            value=f"${current_price:.2f}",
            delta=f"{price_change_pct:+.2f}%"
        )
    
    with col2:
        volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].mean()
        vol_change = ((volume - avg_volume) / avg_volume) * 100
        st.metric(
            label="📊 Volume",
            value=f"{volume:,.0f}",
            delta=f"{vol_change:+.1f}% vs avg"
        )
    
    indicator_calc = get_indicator_calculator()
    rsi = indicator_calc.calculate_rsi(df).iloc[-1]
    
    with col3:
        rsi_status = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
        st.metric(
            label="📈 RSI",
            value=f"{rsi:.1f}",
            delta=rsi_status
        )
    
    # Run anomaly detection
    detector = AnomalyDetector(zscore_threshold=zscore_threshold)
    anomalies = detector.detect_all(df, selected_ticker)
    ensemble_score = detector.get_ensemble_score(df, selected_ticker)
    
    with col4:
        score_status = "🔴 High Risk" if ensemble_score > 0.7 else "🟡 Moderate" if ensemble_score > 0.3 else "🟢 Normal"
        st.metric(
            label="⚠️ Anomaly Score",
            value=f"{ensemble_score:.0%}",
            delta=score_status
        )
    
    st.markdown("---")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Price Chart", "🔮 Forecast", "⚠️ Anomalies", "📈 Indicators"])
    
    with tab1:
        st.subheader("Price Chart with Technical Analysis")
        price_chart = create_price_chart(df, selected_ticker, anomalies)
        st.plotly_chart(price_chart, use_container_width=True)
    
    with tab2:
        st.subheader("Prophet Price Forecast")
        with st.spinner("Generating forecast..."):
            forecast_chart = create_forecast_chart(df, selected_ticker)
            if forecast_chart:
                st.plotly_chart(forecast_chart, use_container_width=True)
            else:
                st.warning("Unable to generate forecast. Need more historical data.")
    
    with tab3:
        st.subheader("Detected Anomalies")
        
        if not anomalies:
            st.success("✅ No anomalies detected in current data!")
        else:
            for anomaly in anomalies:
                priority_class = {
                    "critical": "anomaly-critical",
                    "warning": "anomaly-warning",
                    "info": "anomaly-info"
                }[anomaly.priority.value]
                
                emoji = {"critical": "🔴", "warning": "🟡", "info": "🟢"}[anomaly.priority.value]
                
                with st.container():
                    st.markdown(f"""
                    <div class="{priority_class}">
                        {emoji} <b>{anomaly.anomaly_type.value.replace('_', ' ').title()}</b><br>
                        💰 Price: ${anomaly.current_price:.2f} | ⚠️ Severity: {anomaly.severity:.0%}<br>
                        📝 {anomaly.description}
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab4:
        st.subheader("Technical Indicators Summary")
        
        # Calculate all indicators
        df_with_indicators = indicator_calc.calculate_all(df)
        latest = df_with_indicators.iloc[-1]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### Moving Averages")
            st.write(f"**SMA (20):** ${latest['SMA_20']:.2f}")
            st.write(f"**EMA (12):** ${latest['EMA_12']:.2f}")
            st.write(f"**EMA (26):** ${latest['EMA_26']:.2f}")
        
        with col2:
            st.markdown("### Bollinger Bands")
            st.write(f"**Upper:** ${latest['BB_Upper']:.2f}")
            st.write(f"**Middle:** ${latest['BB_Middle']:.2f}")
            st.write(f"**Lower:** ${latest['BB_Lower']:.2f}")
            st.write(f"**Width:** {latest['BB_Width']:.2%}")
        
        with col3:
            st.markdown("### Momentum")
            st.write(f"**RSI:** {latest['RSI']:.1f}")
            st.write(f"**MACD:** {latest['MACD']:.4f}")
            st.write(f"**Signal:** {latest['MACD_Signal']:.4f}")
            st.write(f"**ATR:** ${latest['ATR']:.2f}")


if __name__ == "__main__":
    main()
