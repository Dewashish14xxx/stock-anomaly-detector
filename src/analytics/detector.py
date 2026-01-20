"""
Stock Anomaly Detector - Anomaly Detection Engine
Ensemble detection using Z-score, volatility, and Prophet deviations
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Optional
from src.config import config
from src.data.models import Anomaly, AnomalyType, AlertPriority
from src.analytics.indicators import TechnicalIndicatorCalculator
from src.analytics.forecaster import StockForecaster
from src.utils.logger import logger


class AnomalyDetector:
    """
    Ensemble anomaly detector combining multiple detection methods:
    1. Z-Score: Statistical deviation from rolling mean
    2. Volatility Spike: ATR exceeds historical percentile
    3. Prophet Deviation: Price outside forecast confidence bounds
    4. Bollinger Breakout: Price outside Bollinger Bands
    5. RSI Extreme: Overbought/Oversold conditions
    """
    
    def __init__(
        self,
        zscore_threshold: float = None,
        volatility_percentile: int = None,
        rsi_overbought: float = 70,
        rsi_oversold: float = 30,
        lookback_period: int = 20
    ):
        """
        Initialize the anomaly detector.
        
        Args:
            zscore_threshold: Z-score threshold for anomaly (default from config)
            volatility_percentile: Percentile for volatility spike (default from config)
            rsi_overbought: RSI level for overbought signal
            rsi_oversold: RSI level for oversold signal
            lookback_period: Rolling window for calculations
        """
        self.zscore_threshold = zscore_threshold or config.anomaly.zscore_threshold
        self.volatility_percentile = volatility_percentile or config.anomaly.volatility_percentile
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.lookback_period = lookback_period
        
        self.indicator_calc = TechnicalIndicatorCalculator()
        self.forecaster = StockForecaster()
        
        logger.info(f"AnomalyDetector initialized: zscore={self.zscore_threshold}, volatility_pct={self.volatility_percentile}")
    
    def detect_zscore_anomaly(self, df: pd.DataFrame, ticker: str) -> List[Anomaly]:
        """
        Detect anomalies using Z-score method.
        Flag prices more than threshold standard deviations from rolling mean.
        """
        anomalies = []
        
        if len(df) < self.lookback_period:
            return anomalies
        
        close = df['Close']
        rolling_mean = close.rolling(window=self.lookback_period).mean()
        rolling_std = close.rolling(window=self.lookback_period).std()
        
        zscore = (close - rolling_mean) / rolling_std
        
        # Check latest value
        if not zscore.empty and not np.isnan(zscore.iloc[-1]):
            latest_zscore = zscore.iloc[-1]
            
            if abs(latest_zscore) > self.zscore_threshold:
                direction = "above" if latest_zscore > 0 else "below"
                severity = min(abs(latest_zscore) / (self.zscore_threshold * 2), 1.0)
                priority = AlertPriority.CRITICAL if severity > 0.7 else AlertPriority.WARNING
                
                timestamp = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else datetime.now()
                
                anomalies.append(Anomaly(
                    ticker=ticker,
                    timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                    anomaly_type=AnomalyType.ZSCORE,
                    severity=severity,
                    current_price=float(close.iloc[-1]),
                    expected_price=float(rolling_mean.iloc[-1]),
                    description=f"Price is {abs(latest_zscore):.1f}σ {direction} the rolling mean",
                    priority=priority
                ))
        
        return anomalies
    
    def detect_volatility_spike(self, df: pd.DataFrame, ticker: str) -> List[Anomaly]:
        """
        Detect volatility spikes using ATR.
        Flag when ATR exceeds historical percentile.
        """
        anomalies = []
        
        if len(df) < 30:  # Need enough data for percentile
            return anomalies
        
        atr = self.indicator_calc.calculate_atr(df)
        
        if atr.empty or atr.isna().all():
            return anomalies
        
        threshold = atr.quantile(self.volatility_percentile / 100)
        latest_atr = atr.iloc[-1]
        
        if not np.isnan(latest_atr) and latest_atr > threshold:
            severity = min((latest_atr - threshold) / threshold, 1.0)
            
            timestamp = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else datetime.now()
            
            anomalies.append(Anomaly(
                ticker=ticker,
                timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                anomaly_type=AnomalyType.VOLATILITY_SPIKE,
                severity=severity,
                current_price=float(df['Close'].iloc[-1]),
                expected_price=None,
                description=f"ATR ({latest_atr:.2f}) exceeds {self.volatility_percentile}th percentile ({threshold:.2f})",
                priority=AlertPriority.WARNING if severity < 0.5 else AlertPriority.CRITICAL
            ))
        
        return anomalies
    
    def detect_bollinger_breakout(self, df: pd.DataFrame, ticker: str) -> List[Anomaly]:
        """
        Detect Bollinger Band breakouts.
        Flag when price moves outside the bands.
        """
        anomalies = []
        
        if len(df) < 20:
            return anomalies
        
        upper, middle, lower = self.indicator_calc.calculate_bollinger_bands(df)
        close = df['Close'].iloc[-1]
        
        timestamp = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else datetime.now()
        
        if close > upper.iloc[-1]:
            deviation = (close - upper.iloc[-1]) / middle.iloc[-1]
            anomalies.append(Anomaly(
                ticker=ticker,
                timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                anomaly_type=AnomalyType.BOLLINGER_BREAKOUT,
                severity=min(deviation * 10, 1.0),
                current_price=float(close),
                expected_price=float(upper.iloc[-1]),
                description=f"Price broke above upper Bollinger Band (${upper.iloc[-1]:.2f})",
                priority=AlertPriority.WARNING
            ))
        elif close < lower.iloc[-1]:
            deviation = (lower.iloc[-1] - close) / middle.iloc[-1]
            anomalies.append(Anomaly(
                ticker=ticker,
                timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                anomaly_type=AnomalyType.BOLLINGER_BREAKOUT,
                severity=min(deviation * 10, 1.0),
                current_price=float(close),
                expected_price=float(lower.iloc[-1]),
                description=f"Price broke below lower Bollinger Band (${lower.iloc[-1]:.2f})",
                priority=AlertPriority.WARNING
            ))
        
        return anomalies
    
    def detect_rsi_extreme(self, df: pd.DataFrame, ticker: str) -> List[Anomaly]:
        """
        Detect RSI extreme conditions (overbought/oversold).
        """
        anomalies = []
        
        if len(df) < 14:
            return anomalies
        
        rsi = self.indicator_calc.calculate_rsi(df)
        latest_rsi = rsi.iloc[-1]
        
        if np.isnan(latest_rsi):
            return anomalies
        
        timestamp = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else datetime.now()
        
        if latest_rsi > self.rsi_overbought:
            severity = (latest_rsi - self.rsi_overbought) / (100 - self.rsi_overbought)
            anomalies.append(Anomaly(
                ticker=ticker,
                timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                anomaly_type=AnomalyType.RSI_EXTREME,
                severity=min(severity, 1.0),
                current_price=float(df['Close'].iloc[-1]),
                description=f"RSI overbought at {latest_rsi:.1f} (threshold: {self.rsi_overbought})",
                priority=AlertPriority.INFO
            ))
        elif latest_rsi < self.rsi_oversold:
            severity = (self.rsi_oversold - latest_rsi) / self.rsi_oversold
            anomalies.append(Anomaly(
                ticker=ticker,
                timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                anomaly_type=AnomalyType.RSI_EXTREME,
                severity=min(severity, 1.0),
                current_price=float(df['Close'].iloc[-1]),
                description=f"RSI oversold at {latest_rsi:.1f} (threshold: {self.rsi_oversold})",
                priority=AlertPriority.INFO
            ))
        
        return anomalies
    
    def detect_prophet_deviation(self, df: pd.DataFrame, ticker: str) -> List[Anomaly]:
        """
        Detect deviations from Prophet forecast.
        """
        anomalies = []
        
        if len(df) < 30:  # Need minimum data for Prophet
            return anomalies
        
        try:
            # Get forecast for current price
            forecast_result = self.forecaster.get_current_forecast(ticker, df)
            
            if forecast_result is None:
                return anomalies
            
            current_price = float(df['Close'].iloc[-1])
            deviation = self.forecaster.check_deviation(ticker, current_price, forecast_result)
            
            if deviation:
                timestamp = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else datetime.now()
                severity = min(deviation['deviation_pct'] / 10, 1.0)  # 10% deviation = max severity
                
                anomalies.append(Anomaly(
                    ticker=ticker,
                    timestamp=timestamp.to_pydatetime() if hasattr(timestamp, 'to_pydatetime') else timestamp,
                    anomaly_type=AnomalyType.PROPHET_DEVIATION,
                    severity=severity,
                    current_price=current_price,
                    expected_price=float(deviation['predicted']),
                    description=f"Price {deviation['deviation_pct']:.1f}% {deviation['direction']} Prophet forecast",
                    priority=AlertPriority.CRITICAL if severity > 0.5 else AlertPriority.WARNING
                ))
        except Exception as e:
            logger.error(f"Prophet deviation detection failed for {ticker}: {e}")
        
        return anomalies
    
    def detect_all(self, df: pd.DataFrame, ticker: str) -> List[Anomaly]:
        """
        Run all anomaly detection methods and return combined results.
        
        Args:
            df: DataFrame with OHLCV data
            ticker: Stock ticker symbol
            
        Returns:
            List of all detected anomalies
        """
        all_anomalies = []
        
        # Run each detector
        all_anomalies.extend(self.detect_zscore_anomaly(df, ticker))
        all_anomalies.extend(self.detect_volatility_spike(df, ticker))
        all_anomalies.extend(self.detect_bollinger_breakout(df, ticker))
        all_anomalies.extend(self.detect_rsi_extreme(df, ticker))
        all_anomalies.extend(self.detect_prophet_deviation(df, ticker))
        
        # Sort by severity (highest first)
        all_anomalies.sort(key=lambda x: x.severity, reverse=True)
        
        if all_anomalies:
            logger.info(f"Detected {len(all_anomalies)} anomalies for {ticker}")
        
        return all_anomalies
    
    def get_ensemble_score(self, df: pd.DataFrame, ticker: str) -> float:
        """
        Calculate ensemble anomaly score (0-1).
        Higher score = more anomalous.
        """
        anomalies = self.detect_all(df, ticker)
        
        if not anomalies:
            return 0.0
        
        # Weighted average of severity scores
        weights = {
            AnomalyType.ZSCORE: 0.3,
            AnomalyType.PROPHET_DEVIATION: 0.25,
            AnomalyType.VOLATILITY_SPIKE: 0.2,
            AnomalyType.BOLLINGER_BREAKOUT: 0.15,
            AnomalyType.RSI_EXTREME: 0.1
        }
        
        total_weight = 0
        weighted_score = 0
        
        for anomaly in anomalies:
            weight = weights.get(anomaly.anomaly_type, 0.1)
            weighted_score += anomaly.severity * weight
            total_weight += weight
        
        return min(weighted_score / total_weight if total_weight else 0, 1.0)
