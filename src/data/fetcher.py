"""
Stock Anomaly Detector - Stock Price Fetcher
Uses yfinance for real-time stock data fetching
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from src.data.models import StockPrice
from src.utils.logger import logger
from src.config import config


class StockFetcher:
    """
    Fetches stock price data using yfinance API.
    Supports both historical and real-time data fetching.
    """
    
    def __init__(self, tickers: Optional[List[str]] = None):
        """
        Initialize the stock fetcher.
        
        Args:
            tickers: List of stock tickers to fetch. Defaults to config tickers.
        """
        self.tickers = tickers or config.stocks.tickers
        logger.info(f"StockFetcher initialized for tickers: {self.tickers}")
    
    def fetch_latest(self, ticker: str, period: str = "1d", interval: str = "5m") -> List[StockPrice]:
        """
        Fetch the latest stock prices for a ticker.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            period: Data period (1d, 5d, 1mo, etc.)
            interval: Data interval (1m, 5m, 15m, 1h, 1d)
            
        Returns:
            List of StockPrice objects
        """
        try:
            logger.debug(f"Fetching {ticker} data: period={period}, interval={interval}")
            
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return []
            
            prices = []
            for timestamp, row in df.iterrows():
                price = StockPrice(
                    ticker=ticker,
                    timestamp=timestamp.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                )
                prices.append(price)
            
            logger.info(f"Fetched {len(prices)} data points for {ticker}")
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            return []
    
    def fetch_historical(
        self, 
        ticker: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "1mo"
    ) -> pd.DataFrame:
        """
        Fetch historical daily data for analysis and model training.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            period: Period if dates not specified
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            stock = yf.Ticker(ticker)
            
            if start_date and end_date:
                df = stock.history(start=start_date, end=end_date)
            else:
                df = stock.history(period=period)
            
            logger.info(f"Fetched {len(df)} historical records for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {e}")
            return pd.DataFrame()
    
    def fetch_all_tickers(self, period: str = "1d", interval: str = "5m") -> dict:
        """
        Fetch latest data for all configured tickers.
        
        Returns:
            Dict mapping ticker -> List[StockPrice]
        """
        results = {}
        for ticker in self.tickers:
            results[ticker] = self.fetch_latest(ticker, period, interval)
        return results
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get the current/latest price for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Current price or None if unavailable
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get('regularMarketPrice') or info.get('currentPrice')
        except Exception as e:
            logger.error(f"Error getting current price for {ticker}: {e}")
            return None
