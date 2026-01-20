"""
Stock Anomaly Detector - Configuration Management
"""
import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    chat_id: str = field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    
    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)


@dataclass
class StockConfig:
    """Stock fetching configuration"""
    tickers: List[str] = field(default_factory=lambda: os.getenv("STOCK_TICKERS", "AAPL,GOOGL,MSFT,TSLA").split(","))
    fetch_interval_minutes: int = field(default_factory=lambda: int(os.getenv("FETCH_INTERVAL_MINUTES", "5")))


@dataclass
class AnomalyConfig:
    """Anomaly detection thresholds"""
    zscore_threshold: float = field(default_factory=lambda: float(os.getenv("ZSCORE_THRESHOLD", "3.0")))
    volatility_percentile: int = field(default_factory=lambda: int(os.getenv("VOLATILITY_PERCENTILE", "95")))
    prophet_confidence_level: float = field(default_factory=lambda: float(os.getenv("PROPHET_CONFIDENCE_LEVEL", "0.95")))


@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data/stocks.db"))


@dataclass
class Config:
    """Main configuration container"""
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    stocks: StockConfig = field(default_factory=StockConfig)
    anomaly: AnomalyConfig = field(default_factory=AnomalyConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


# Global config instance
config = Config()
