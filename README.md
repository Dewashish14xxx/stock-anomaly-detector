# 📈 Real-Time Stock Price Anomaly Detector

A production-ready anomaly detection system that monitors stock prices in real-time, uses Prophet for forecasting, calculates technical indicators, and alerts users via Telegram when abnormal patterns are detected.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29-FF4B4B)
![Prophet](https://img.shields.io/badge/Prophet-1.1-purple)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## ✨ Features

- **Real-Time Data Ingestion**: Fetches live stock data using yfinance (12,000+ datapoints/day)
- **Technical Indicators**: RSI, MACD, Bollinger Bands, ATR calculations
- **Prophet Forecasting**: Time-series predictions with confidence intervals
- **Ensemble Anomaly Detection**: Combines Z-score, volatility, and forecast deviation methods
- **Interactive Dashboard**: Streamlit-powered visualization with Plotly charts
- **Telegram Alerts**: Instant notifications for detected anomalies
- **Docker Ready**: Containerized for easy deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip

### Installation

1. **Clone the repository**
   ```bash
   cd stock-anomaly-detector
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy .env.example .env
   # Edit .env with your Telegram credentials (optional)
   ```

5. **Run the dashboard**
   ```bash
   streamlit run app/streamlit_app.py
   ```

6. **Open in browser**: http://localhost:8501

## 🐳 Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## ☁️ Streamlit Cloud Deployment (FREE)

1. Push code to public GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Select `app/streamlit_app.py` as main file
5. Add secrets in Streamlit Cloud settings:
   ```toml
   TELEGRAM_BOT_TOKEN = "your_token"
   TELEGRAM_CHAT_ID = "your_chat_id"
   ```
6. Deploy! 🎉

## 📱 Setting Up Telegram Alerts

1. Create a bot via [@BotFather](https://t.me/botfather):
   - Send `/newbot` and follow prompts
   - Copy the bot token

2. Get your Chat ID:
   - Start a chat with your bot
   - Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Find your `chat.id` in the response

3. Add to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

## 🔧 Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `STOCK_TICKERS` | `AAPL,GOOGL,MSFT,TSLA` | Comma-separated ticker symbols |
| `FETCH_INTERVAL_MINUTES` | `5` | Data refresh interval |
| `ZSCORE_THRESHOLD` | `3.0` | Z-score for anomaly detection |
| `VOLATILITY_PERCENTILE` | `95` | ATR percentile threshold |

## 📊 Anomaly Detection Methods

| Method | Description | Severity |
|--------|-------------|----------|
| **Z-Score** | Price deviation from rolling mean (>3σ) | High |
| **Prophet Deviation** | Outside forecast confidence bands | High |
| **Volatility Spike** | ATR exceeds 95th percentile | Medium |
| **Bollinger Breakout** | Price outside Bollinger Bands | Medium |
| **RSI Extreme** | Overbought (>70) / Oversold (<30) | Low |

## 🏗️ Project Structure

```
stock-anomaly-detector/
├── src/
│   ├── config.py          # Configuration management
│   ├── scheduler.py       # Background job runner
│   ├── data/
│   │   ├── fetcher.py     # yfinance data fetching
│   │   ├── storage.py     # SQLite/BigQuery storage
│   │   └── models.py      # Data models
│   ├── analytics/
│   │   ├── indicators.py  # Technical indicators
│   │   ├── forecaster.py  # Prophet forecasting
│   │   └── detector.py    # Anomaly detection
│   └── alerts/
│       └── telegram.py    # Telegram integration
├── app/
│   └── streamlit_app.py   # Dashboard
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 📈 Dashboard Preview

The Streamlit dashboard includes:
- **Price Chart**: Candlestick with Bollinger Bands overlay
- **Technical Indicators**: RSI and MACD panels
- **Prophet Forecast**: 30-day predictions with confidence intervals
- **Anomaly Alerts**: Real-time anomaly notifications
- **Metrics**: Current price, volume, RSI, and anomaly score

## 🧪 Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

## 📝 License

MIT License - feel free to use for personal or commercial projects.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

**Built with ❤️ using Python, Streamlit, and Prophet**
