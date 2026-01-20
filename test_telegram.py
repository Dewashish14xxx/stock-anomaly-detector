"""
Quick test script to send a test alert via Telegram
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.alerts.telegram import TelegramAlerter
from src.data.models import Anomaly, AnomalyType, AlertPriority
from datetime import datetime

async def send_test_alert():
    alerter = TelegramAlerter()
    
    print("Testing Telegram bot connection...")
    
    if not alerter.is_configured:
        print("❌ Telegram not configured! Check your .env file.")
        return
    
    # Create a test anomaly
    test_anomaly = Anomaly(
        ticker="TEST",
        timestamp=datetime.now(),
        anomaly_type=AnomalyType.ZSCORE,
        severity=0.85,
        current_price=250.00,
        expected_price=245.00,
        description="This is a TEST alert to verify Telegram integration!",
        priority=AlertPriority.WARNING
    )
    
    print("Sending test alert...")
    success = await alerter.send_alert_async(test_anomaly, force=True)
    
    if success:
        print("✅ Test alert sent successfully! Check your Telegram.")
    else:
        print("❌ Failed to send alert. Check your bot token and chat ID.")

if __name__ == "__main__":
    asyncio.run(send_test_alert())
