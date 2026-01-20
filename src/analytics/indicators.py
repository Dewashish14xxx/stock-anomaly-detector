"""
Stock Anomaly Detector - Technical Indicators
Calculates RSI, MACD, Bollinger Bands, and ATR
"""
import pandas as pd
import numpy as np
from typing import Optional
from src.utils.logger import logger


class TechnicalIndicatorCalculator:
    """
    Calculates technical indicators for stock price data.
    All methods accept a DataFrame with OHLCV columns.
    """
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'Close') -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss
        
        Args:
            df: DataFrame with price data
            period: RSI period (default 14)
            column: Column to use for calculation
            
        Returns:
            Series with RSI values
        """
        delta = df[column].diff()
        
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period, min_periods=1).mean()
        avg_loss = loss.rolling(window=period, min_periods=1).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_macd(
        df: pd.DataFrame, 
        fast_period: int = 12, 
        slow_period: int = 26, 
        signal_period: int = 9,
        column: str = 'Close'
    ) -> tuple:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        MACD Line = 12-day EMA - 26-day EMA
        Signal Line = 9-day EMA of MACD Line
        Histogram = MACD Line - Signal Line
        
        Args:
            df: DataFrame with price data
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)
            column: Column to use
            
        Returns:
            Tuple of (macd_line, signal_line, histogram)
        """
        ema_fast = df[column].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df[column].ewm(span=slow_period, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame, 
        period: int = 20, 
        std_dev: float = 2.0,
        column: str = 'Close'
    ) -> tuple:
        """
        Calculate Bollinger Bands.
        
        Middle Band = 20-day SMA
        Upper Band = Middle Band + (2 * 20-day standard deviation)
        Lower Band = Middle Band - (2 * 20-day standard deviation)
        
        Args:
            df: DataFrame with price data
            period: Moving average period (default 20)
            std_dev: Standard deviation multiplier (default 2)
            column: Column to use
            
        Returns:
            Tuple of (upper_band, middle_band, lower_band)
        """
        middle = df[column].rolling(window=period).mean()
        std = df[column].rolling(window=period).std()
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        
        return upper, middle, lower
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR) - volatility indicator.
        
        True Range is the greatest of:
        - Current High - Current Low
        - |Current High - Previous Close|
        - |Current Low - Previous Close|
        
        ATR = Moving average of True Range
        
        Args:
            df: DataFrame with OHLC data
            period: ATR period (default 14)
            
        Returns:
            Series with ATR values
        """
        high = df['High']
        low = df['Low']
        close = df['Close']
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20, column: str = 'Close') -> pd.Series:
        """Calculate Simple Moving Average"""
        return df[column].rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 12, column: str = 'Close') -> pd.Series:
        """Calculate Exponential Moving Average"""
        return df[column].ewm(span=period, adjust=False).mean()
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all technical indicators and add to DataFrame.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with all indicators added
        """
        result = df.copy()
        
        # RSI
        result['RSI'] = self.calculate_rsi(df)
        
        # MACD
        macd, signal, hist = self.calculate_macd(df)
        result['MACD'] = macd
        result['MACD_Signal'] = signal
        result['MACD_Histogram'] = hist
        
        # Bollinger Bands
        upper, middle, lower = self.calculate_bollinger_bands(df)
        result['BB_Upper'] = upper
        result['BB_Middle'] = middle
        result['BB_Lower'] = lower
        
        # ATR
        result['ATR'] = self.calculate_atr(df)
        
        # Moving Averages
        result['SMA_20'] = self.calculate_sma(df, 20)
        result['EMA_12'] = self.calculate_ema(df, 12)
        result['EMA_26'] = self.calculate_ema(df, 26)
        
        # Bollinger Band Width (for volatility analysis)
        result['BB_Width'] = (result['BB_Upper'] - result['BB_Lower']) / result['BB_Middle']
        
        # Price position within Bollinger Bands (0 = lower band, 1 = upper band)
        result['BB_Position'] = (df['Close'] - result['BB_Lower']) / (result['BB_Upper'] - result['BB_Lower'])
        
        logger.debug(f"Calculated all indicators for {len(df)} data points")
        return result
