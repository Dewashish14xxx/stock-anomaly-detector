"""
Stock Anomaly Detector - Scheduler
Background job for continuous data ingestion and anomaly detection
"""
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from src.config import config
from src.data.fetcher import StockFetcher
from src.data.storage import DataStorage
from src.analytics.detector import AnomalyDetector
from src.alerts.telegram import TelegramAlerter
from src.utils.logger import logger


class AnomalyScheduler:
    """
    Scheduled job runner for continuous monitoring.
    Periodically fetches data, runs detection, and sends alerts.
    """
    
    def __init__(self):
        self.fetcher = StockFetcher()
        self.storage = DataStorage()
        self.detector = AnomalyDetector()
        self.alerter = TelegramAlerter()
        self.scheduler = BlockingScheduler()
        
        logger.info("AnomalyScheduler initialized")
    
    def run_detection_cycle(self):
        """
        Run a single detection cycle:
        1. Fetch latest data for all tickers
        2. Run anomaly detection
        3. Send alerts for detected anomalies
        4. Store results
        """
        logger.info(f"Starting detection cycle at {datetime.now()}")
        
        for ticker in config.stocks.tickers:
            try:
                # Fetch historical data for analysis
                df = self.fetcher.fetch_historical(ticker, period="1mo")
                
                if df.empty:
                    logger.warning(f"No data for {ticker}, skipping")
                    continue
                
                # Store latest prices
                prices = self.fetcher.fetch_latest(ticker, period="1d", interval="5m")
                self.storage.save_prices(prices)
                
                # Run anomaly detection
                anomalies = self.detector.detect_all(df, ticker)
                
                # Process anomalies
                for anomaly in anomalies:
                    # Save to database
                    self.storage.save_anomaly(anomaly)
                    
                    # Send alert (alerter handles throttling)
                    self.alerter.send_alert(anomaly)
                
                logger.info(f"Processed {ticker}: {len(anomalies)} anomalies detected")
                
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
        
        logger.info("Detection cycle completed")
    
    def start(self):
        """Start the scheduler"""
        interval_minutes = config.stocks.fetch_interval_minutes
        
        # Add job with configured interval
        self.scheduler.add_job(
            self.run_detection_cycle,
            IntervalTrigger(minutes=interval_minutes),
            id='detection_cycle',
            name='Stock Anomaly Detection',
            next_run_time=datetime.now()  # Run immediately on start
        )
        
        logger.info(f"Scheduler started with {interval_minutes} minute interval")
        
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")
            self.storage.close()


def main():
    """Entry point for scheduler"""
    scheduler = AnomalyScheduler()
    scheduler.start()


if __name__ == "__main__":
    main()
