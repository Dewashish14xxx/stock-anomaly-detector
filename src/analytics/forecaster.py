"""
Stock Anomaly Detector - Prophet Forecaster
Time-series forecasting using Facebook Prophet
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Tuple
from prophet import Prophet
from src.config import config
from src.utils.logger import logger


class StockForecaster:
    """
    Prophet-based stock price forecaster.
    Provides predictions with confidence intervals.
    """
    
    def __init__(
        self, 
        confidence_level: float = 0.95,
        yearly_seasonality: bool = True,
        weekly_seasonality: bool = True,
        daily_seasonality: bool = False
    ):
        """
        Initialize the forecaster.
        
        Args:
            confidence_level: Confidence interval level (default 0.95)
            yearly_seasonality: Include yearly patterns
            weekly_seasonality: Include weekly patterns
            daily_seasonality: Include daily patterns (for intraday)
        """
        self.confidence_level = confidence_level
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
        self.models = {}  # Cache trained models by ticker
        
        logger.info(f"StockForecaster initialized with {confidence_level:.0%} confidence")
    
    def _prepare_data(self, df: pd.DataFrame, price_column: str = 'Close') -> pd.DataFrame:
        """
        Prepare data for Prophet (requires 'ds' and 'y' columns).
        
        Args:
            df: DataFrame with datetime index and price column
            price_column: Column name for price values
            
        Returns:
            DataFrame formatted for Prophet
        """
        prophet_df = pd.DataFrame()
        
        # Handle both index and column timestamps
        if isinstance(df.index, pd.DatetimeIndex):
            prophet_df['ds'] = df.index.tz_localize(None) if df.index.tz else df.index
        elif 'timestamp' in df.columns:
            prophet_df['ds'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
        elif 'Date' in df.columns:
            prophet_df['ds'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
        
        prophet_df['y'] = df[price_column].values
        
        return prophet_df.dropna()
    
    def train(self, ticker: str, df: pd.DataFrame, price_column: str = 'Close') -> bool:
        """
        Train a Prophet model for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol
            df: Historical price data
            price_column: Column with price values
            
        Returns:
            True if training successful
        """
        try:
            prophet_df = self._prepare_data(df, price_column)
            
            if len(prophet_df) < 30:
                logger.warning(f"Insufficient data for {ticker}: {len(prophet_df)} records")
                return False
            
            # Create and configure Prophet model
            model = Prophet(
                interval_width=self.confidence_level,
                yearly_seasonality=self.yearly_seasonality,
                weekly_seasonality=self.weekly_seasonality,
                daily_seasonality=self.daily_seasonality,
                changepoint_prior_scale=0.05  # Flexibility for trend changes
            )
            
            # Suppress Prophet's verbose output
            model.fit(prophet_df)
            
            self.models[ticker] = {
                'model': model,
                'last_trained': datetime.now(),
                'data_points': len(prophet_df)
            }
            
            logger.info(f"Trained Prophet model for {ticker} with {len(prophet_df)} data points")
            return True
            
        except Exception as e:
            logger.error(f"Error training model for {ticker}: {e}")
            return False
    
    def forecast(
        self, 
        ticker: str, 
        periods: int = 5,
        freq: str = 'D'
    ) -> Optional[pd.DataFrame]:
        """
        Generate forecast for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            periods: Number of periods to forecast
            freq: Frequency ('D' for daily, 'H' for hourly)
            
        Returns:
            DataFrame with forecast, lower/upper bounds
        """
        if ticker not in self.models:
            logger.warning(f"No trained model for {ticker}")
            return None
        
        try:
            model = self.models[ticker]['model']
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=periods, freq=freq)
            
            # Generate forecast
            forecast = model.predict(future)
            
            # Extract relevant columns
            result = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).copy()
            result.columns = ['timestamp', 'predicted', 'lower_bound', 'upper_bound']
            result['ticker'] = ticker
            
            logger.debug(f"Generated {periods}-period forecast for {ticker}")
            return result
            
        except Exception as e:
            logger.error(f"Error forecasting for {ticker}: {e}")
            return None
    
    def get_current_forecast(
        self, 
        ticker: str, 
        current_df: pd.DataFrame,
        price_column: str = 'Close'
    ) -> Optional[Tuple[float, float, float]]:
        """
        Get forecast for current time period with bounds.
        
        Args:
            ticker: Stock ticker
            current_df: Current price data
            price_column: Price column name
            
        Returns:
            Tuple of (predicted, lower_bound, upper_bound) or None
        """
        if ticker not in self.models:
            # Train on available data first
            if not self.train(ticker, current_df, price_column):
                return None
        
        forecast_df = self.forecast(ticker, periods=1)
        
        if forecast_df is None or forecast_df.empty:
            return None
        
        row = forecast_df.iloc[0]
        return (row['predicted'], row['lower_bound'], row['upper_bound'])
    
    def check_deviation(
        self, 
        ticker: str, 
        actual_price: float,
        forecast_result: Tuple[float, float, float]
    ) -> Optional[dict]:
        """
        Check if actual price deviates from forecast.
        
        Args:
            ticker: Stock ticker
            actual_price: Current actual price
            forecast_result: Tuple from get_current_forecast
            
        Returns:
            Dict with deviation info or None if no anomaly
        """
        predicted, lower, upper = forecast_result
        
        if actual_price < lower:
            deviation = (lower - actual_price) / predicted
            return {
                'ticker': ticker,
                'direction': 'below',
                'actual': actual_price,
                'predicted': predicted,
                'bound': lower,
                'deviation_pct': deviation * 100
            }
        elif actual_price > upper:
            deviation = (actual_price - upper) / predicted
            return {
                'ticker': ticker,
                'direction': 'above',
                'actual': actual_price,
                'predicted': predicted,
                'bound': upper,
                'deviation_pct': deviation * 100
            }
        
        return None
    
    def retrain_if_stale(self, ticker: str, df: pd.DataFrame, max_age_hours: int = 24) -> bool:
        """
        Retrain model if it's older than max_age_hours.
        
        Args:
            ticker: Stock ticker
            df: Current data for retraining
            max_age_hours: Maximum model age before retraining
            
        Returns:
            True if retrained, False if still fresh
        """
        if ticker not in self.models:
            return self.train(ticker, df)
        
        last_trained = self.models[ticker]['last_trained']
        age = datetime.now() - last_trained
        
        if age > timedelta(hours=max_age_hours):
            logger.info(f"Retraining stale model for {ticker} (age: {age})")
            return self.train(ticker, df)
        
        return False
