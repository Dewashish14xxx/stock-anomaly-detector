# 📈 Real-Time Stock Price Anomaly Detector

> A personal project I built to learn about stock market analysis, machine learning forecasting, and real-time dashboards!

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://stock-anomaly-detector-r5u95r5p6fgde4ssrfd2ox.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)](https://python.org)
[![Prophet](https://img.shields.io/badge/ML-Prophet-purple?style=flat-square)](https://facebook.github.io/prophet/)

## 🎯 What This Project Does

This is a **stock market monitoring tool** that I built to detect unusual price movements (anomalies) in stocks. It uses:

- **Prophet** (by Meta/Facebook) for predicting future stock prices
- **Technical indicators** like RSI, MACD, and Bollinger Bands that traders actually use
- **Real-time data** from yfinance API
- **Telegram bot** that sends me alerts when something unusual happens!

## 🌐 Try It Live!

👉 **[Click here to see the live demo!](https://stock-anomaly-detector-r5u95r5p6fgde4ssrfd2ox.streamlit.app/)**

No installation needed - just open the link and start exploring stocks!

## ✨ Features I Implemented

| Feature | What It Does |
|---------|--------------|
| 📊 **30+ Stocks** | US Tech (Apple, Google, Tesla), Indian (Reliance, TCS), Commodities (Gold, Silver), Indices (Nifty 50) |
| 🔮 **Prophet Forecasting** | Predicts stock prices for next 30 days with confidence intervals |
| 📈 **Technical Analysis** | RSI, MACD, Bollinger Bands, ATR - the same indicators traders use! |
| ⚠️ **Anomaly Detection** | Alerts when prices move unusually using 5 different methods |
| 🔄 **Real-Time Updates** | Auto-refresh every 5-60 seconds (configurable) |
| 📱 **Telegram Alerts** | Get notified on your phone when anomalies are detected |
| 🐳 **Docker Ready** | Can be deployed anywhere with Docker |

## 🛠️ Tech Stack

- **Python 3.11** - Main programming language
- **Streamlit** - For building the interactive dashboard
- **Prophet** - Facebook's time-series forecasting library
- **Pandas & NumPy** - Data manipulation
- **Plotly** - Interactive charts
- **SQLite/SQLAlchemy** - Database storage
- **python-telegram-bot** - Telegram integration
- **Docker** - Containerization

## 📸 Screenshots

The dashboard shows:
- Live stock prices with candlestick charts
- Bollinger Bands for volatility
- RSI and MACD indicators
- Detected anomalies marked on the chart
- Prophet forecasts with confidence bands

## 🚀 How to Run Locally

If you want to run this on your own computer:

```bash
# Clone the repo
git clone https://github.com/Dewashish14xxx/stock-anomaly-detector.git
cd stock-anomaly-detector

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app/streamlit_app.py
```

Then open **http://localhost:8501** in your browser!

## 📁 Project Structure

```
stock-anomaly-detector/
├── app/
│   └── streamlit_app.py    # Main dashboard
├── src/
│   ├── analytics/          # Indicators, forecasting, detection
│   ├── data/               # Data fetching and storage
│   └── alerts/             # Telegram integration
├── Dockerfile              # Docker setup
├── docker-compose.yml
└── requirements.txt
```

## 💡 What I Learned

Building this project taught me:
- How to work with **time-series data** and financial APIs
- Using **Prophet** for ML-based forecasting
- Building **interactive dashboards** with Streamlit
- Integrating **Telegram bots** for notifications
- **Docker containerization** for deployment
- Writing clean, modular Python code

## 🔮 Future Improvements

Things I want to add:
- [ ] More stocks and crypto support
- [ ] Email notifications
- [ ] Historical anomaly analysis
- [ ] Mobile-responsive design
- [ ] User authentication

## 📫 Connect With Me

Feel free to reach out if you have questions about this project!

- GitHub: [@Dewashish14xxx](https://github.com/Dewashish14xxx)

---

*Built as a learning project to understand stock market analysis and ML forecasting* 🚀
