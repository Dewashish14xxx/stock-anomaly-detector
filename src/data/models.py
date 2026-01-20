"""
Stock Anomaly Detector - Data Models
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class AnomalyType(Enum):
    """Types of detected anomalies"""
    ZSCORE = "zscore"
    VOLATILITY_SPIKE = "volatility_spike"
    PROPHET_DEVIATION = "prophet_deviation"
    BOLLINGER_BREAKOUT = "bollinger_breakout"
    RSI_EXTREME = "rsi_extreme"


class AlertPriority(Enum):
    """Alert priority levels"""
    CRITICAL = "critical"  # 🔴
    WARNING = "warning"    # 🟡
    INFO = "info"          # 🟢


@dataclass
class StockPrice:
    """Stock price data point"""
    ticker: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    @property
    def typical_price(self) -> float:
        """Calculate typical price (HLC/3)"""
        return (self.high + self.low + self.close) / 3


@dataclass
class TechnicalIndicators:
    """Technical indicators for a stock at a point in time"""
    ticker: str
    timestamp: datetime
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr: Optional[float] = None
    sma_20: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None


@dataclass
class Forecast:
    """Prophet forecast data"""
    ticker: str
    timestamp: datetime
    forecast_date: datetime
    predicted: float
    lower_bound: float
    upper_bound: float
    

@dataclass
class Anomaly:
    """Detected anomaly"""
    ticker: str
    timestamp: datetime
    anomaly_type: AnomalyType
    severity: float  # 0-1 score
    current_price: float
    expected_price: Optional[float] = None
    description: str = ""
    priority: AlertPriority = AlertPriority.INFO
    
    def to_alert_message(self) -> str:
        """Format anomaly as alert message"""
        emoji = {
            AlertPriority.CRITICAL: "🔴",
            AlertPriority.WARNING: "🟡",
            AlertPriority.INFO: "🟢"
        }[self.priority]
        
        return (
            f"{emoji} **{self.ticker} ANOMALY DETECTED**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 Type: {self.anomaly_type.value.replace('_', ' ').title()}\n"
            f"💰 Price: ${self.current_price:.2f}\n"
            f"📈 Expected: ${self.expected_price:.2f}\n" if self.expected_price else ""
            f"⚠️ Severity: {self.severity:.1%}\n"
            f"📝 {self.description}\n"
            f"🕐 {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )
