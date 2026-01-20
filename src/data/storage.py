"""
Stock Anomaly Detector - Data Storage Layer
SQLite storage with BigQuery-compatible schema
"""
from datetime import datetime
from typing import List, Optional
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.config import config
from src.data.models import StockPrice, Anomaly, AnomalyType, AlertPriority
from src.utils.logger import logger

Base = declarative_base()


class StockPriceTable(Base):
    """SQLAlchemy model for stock prices"""
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnomalyTable(Base):
    """SQLAlchemy model for detected anomalies"""
    __tablename__ = 'anomalies'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    anomaly_type = Column(String(50), nullable=False)
    severity = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    expected_price = Column(Float, nullable=True)
    description = Column(String(500), nullable=True)
    priority = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ForecastTable(Base):
    """SQLAlchemy model for Prophet forecasts"""
    __tablename__ = 'forecasts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    forecast_date = Column(DateTime, nullable=False, index=True)
    predicted = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AlertHistoryTable(Base):
    """SQLAlchemy model for sent alerts"""
    __tablename__ = 'alert_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False, index=True)
    anomaly_type = Column(String(50), nullable=False)
    message = Column(String(1000), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)


class DataStorage:
    """
    Data storage layer using SQLite with SQLAlchemy ORM.
    Schema is designed to be BigQuery-compatible for easy migration.
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the data storage.
        
        Args:
            db_url: Database URL. Defaults to config value.
        """
        self.db_url = db_url or config.database.url
        
        # Ensure data directory exists for SQLite
        if self.db_url.startswith("sqlite"):
            db_path = self.db_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(self.db_url, echo=False)
        Base.metadata.create_all(self.engine)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        logger.info(f"DataStorage initialized with {self.db_url}")
    
    def save_prices(self, prices: List[StockPrice]) -> int:
        """
        Save stock prices to database.
        
        Args:
            prices: List of StockPrice objects
            
        Returns:
            Number of records saved
        """
        try:
            for price in prices:
                record = StockPriceTable(
                    ticker=price.ticker,
                    timestamp=price.timestamp,
                    open=price.open,
                    high=price.high,
                    low=price.low,
                    close=price.close,
                    volume=price.volume
                )
                self.session.merge(record)  # Use merge to handle duplicates
            
            self.session.commit()
            logger.debug(f"Saved {len(prices)} price records")
            return len(prices)
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving prices: {e}")
            return 0
    
    def save_anomaly(self, anomaly: Anomaly) -> bool:
        """
        Save detected anomaly to database.
        
        Args:
            anomaly: Anomaly object
            
        Returns:
            True if saved successfully
        """
        try:
            record = AnomalyTable(
                ticker=anomaly.ticker,
                timestamp=anomaly.timestamp,
                anomaly_type=anomaly.anomaly_type.value,
                severity=anomaly.severity,
                current_price=anomaly.current_price,
                expected_price=anomaly.expected_price,
                description=anomaly.description,
                priority=anomaly.priority.value
            )
            self.session.add(record)
            self.session.commit()
            logger.info(f"Saved anomaly for {anomaly.ticker}: {anomaly.anomaly_type.value}")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error saving anomaly: {e}")
            return False
    
    def get_recent_prices(self, ticker: str, limit: int = 100) -> List[dict]:
        """
        Get recent price records for a ticker.
        
        Args:
            ticker: Stock ticker
            limit: Maximum number of records
            
        Returns:
            List of price records as dicts
        """
        records = (
            self.session.query(StockPriceTable)
            .filter(StockPriceTable.ticker == ticker)
            .order_by(StockPriceTable.timestamp.desc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                'ticker': r.ticker,
                'timestamp': r.timestamp,
                'open': r.open,
                'high': r.high,
                'low': r.low,
                'close': r.close,
                'volume': r.volume
            }
            for r in reversed(records)  # Return in chronological order
        ]
    
    def get_recent_anomalies(self, ticker: Optional[str] = None, limit: int = 50) -> List[dict]:
        """
        Get recent anomalies.
        
        Args:
            ticker: Optional ticker filter
            limit: Maximum number of records
            
        Returns:
            List of anomaly records as dicts
        """
        query = self.session.query(AnomalyTable)
        
        if ticker:
            query = query.filter(AnomalyTable.ticker == ticker)
        
        records = query.order_by(AnomalyTable.timestamp.desc()).limit(limit).all()
        
        return [
            {
                'ticker': r.ticker,
                'timestamp': r.timestamp,
                'anomaly_type': r.anomaly_type,
                'severity': r.severity,
                'current_price': r.current_price,
                'expected_price': r.expected_price,
                'description': r.description,
                'priority': r.priority
            }
            for r in records
        ]
    
    def log_alert(self, ticker: str, anomaly_type: str, message: str) -> bool:
        """Log a sent alert to history"""
        try:
            record = AlertHistoryTable(
                ticker=ticker,
                anomaly_type=anomaly_type,
                message=message
            )
            self.session.add(record)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error logging alert: {e}")
            return False
    
    def get_last_alert_time(self, ticker: str) -> Optional[datetime]:
        """Get the timestamp of the last alert for a ticker"""
        record = (
            self.session.query(AlertHistoryTable)
            .filter(AlertHistoryTable.ticker == ticker)
            .order_by(AlertHistoryTable.sent_at.desc())
            .first()
        )
        return record.sent_at if record else None
    
    def close(self):
        """Close database connection"""
        self.session.close()
        logger.info("DataStorage connection closed")
