"""
Stock Anomaly Detector - Telegram Alerts
Send anomaly notifications via Telegram bot
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from telegram import Bot
from telegram.constants import ParseMode
from src.config import config
from src.data.models import Anomaly, AlertPriority
from src.utils.logger import logger


class TelegramAlerter:
    """
    Sends anomaly alerts via Telegram bot.
    Includes throttling to prevent alert spam.
    """
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        throttle_minutes: int = 15
    ):
        """
        Initialize the Telegram alerter.
        
        Args:
            bot_token: Telegram bot token (from BotFather)
            chat_id: Chat ID to send alerts to
            throttle_minutes: Minimum time between alerts for same ticker
        """
        self.bot_token = bot_token or config.telegram.bot_token
        self.chat_id = chat_id or config.telegram.chat_id
        self.throttle_minutes = throttle_minutes
        
        # Track last alert time per ticker to prevent spam
        self._last_alert_times: dict = {}
        
        if self.is_configured:
            self.bot = Bot(token=self.bot_token)
            logger.info("TelegramAlerter initialized successfully")
        else:
            self.bot = None
            logger.warning("Telegram not configured - alerts will be logged only")
    
    @property
    def is_configured(self) -> bool:
        """Check if Telegram credentials are configured"""
        return bool(self.bot_token and self.chat_id)
    
    def _should_throttle(self, ticker: str) -> bool:
        """Check if we should throttle alerts for this ticker"""
        if ticker not in self._last_alert_times:
            return False
        
        elapsed = datetime.now() - self._last_alert_times[ticker]
        return elapsed < timedelta(minutes=self.throttle_minutes)
    
    def _update_throttle(self, ticker: str):
        """Update the last alert time for throttling"""
        self._last_alert_times[ticker] = datetime.now()
    
    def format_alert(self, anomaly: Anomaly) -> str:
        """
        Format an anomaly as a Telegram message.
        
        Args:
            anomaly: Anomaly object to format
            
        Returns:
            Formatted message string
        """
        emoji = {
            AlertPriority.CRITICAL: "🔴",
            AlertPriority.WARNING: "🟡",
            AlertPriority.INFO: "🟢"
        }[anomaly.priority]
        
        type_emoji = {
            "zscore": "📊",
            "volatility_spike": "📈",
            "prophet_deviation": "🔮",
            "bollinger_breakout": "💥",
            "rsi_extreme": "⚡"
        }
        
        type_icon = type_emoji.get(anomaly.anomaly_type.value, "⚠️")
        
        message = f"""
{emoji} *{anomaly.ticker} ANOMALY DETECTED* {emoji}
━━━━━━━━━━━━━━━━━━━━

{type_icon} *Type:* {anomaly.anomaly_type.value.replace('_', ' ').title()}
💰 *Current Price:* ${anomaly.current_price:.2f}
"""
        
        if anomaly.expected_price:
            diff = anomaly.current_price - anomaly.expected_price
            diff_pct = (diff / anomaly.expected_price) * 100
            direction = "📈" if diff > 0 else "📉"
            message += f"📊 *Expected:* ${anomaly.expected_price:.2f}\n"
            message += f"{direction} *Deviation:* {diff_pct:+.2f}%\n"
        
        severity_bar = "█" * int(anomaly.severity * 10) + "░" * (10 - int(anomaly.severity * 10))
        message += f"""
⚠️ *Severity:* [{severity_bar}] {anomaly.severity:.0%}
📝 {anomaly.description}

🕐 {anomaly.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        return message.strip()
    
    async def send_alert_async(self, anomaly: Anomaly, force: bool = False) -> bool:
        """
        Send an alert asynchronously.
        
        Args:
            anomaly: Anomaly to alert about
            force: If True, ignore throttling
            
        Returns:
            True if sent successfully
        """
        if not force and self._should_throttle(anomaly.ticker):
            logger.debug(f"Throttled alert for {anomaly.ticker}")
            return False
        
        message = self.format_alert(anomaly)
        
        if not self.is_configured:
            logger.info(f"[MOCK ALERT] {anomaly.ticker}: {anomaly.anomaly_type.value}")
            print(f"\n{'='*50}")
            print(message)
            print(f"{'='*50}\n")
            self._update_throttle(anomaly.ticker)
            return True
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"Sent Telegram alert for {anomaly.ticker}")
            self._update_throttle(anomaly.ticker)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False
    
    def send_alert(self, anomaly: Anomaly, force: bool = False) -> bool:
        """
        Send an alert (synchronous wrapper).
        
        Args:
            anomaly: Anomaly to alert about
            force: If True, ignore throttling
            
        Returns:
            True if sent successfully
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_alert_async(anomaly, force))
    
    async def send_summary_async(self, anomalies: list, ticker: Optional[str] = None) -> bool:
        """
        Send a summary of multiple anomalies.
        
        Args:
            anomalies: List of Anomaly objects
            ticker: Optional ticker filter
            
        Returns:
            True if sent successfully
        """
        if not anomalies:
            return True
        
        if ticker:
            anomalies = [a for a in anomalies if a.ticker == ticker]
        
        summary = f"""
📊 *ANOMALY SUMMARY REPORT*
━━━━━━━━━━━━━━━━━━━━

📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
🔢 Total Anomalies: {len(anomalies)}

"""
        
        # Group by priority
        critical = [a for a in anomalies if a.priority == AlertPriority.CRITICAL]
        warning = [a for a in anomalies if a.priority == AlertPriority.WARNING]
        info = [a for a in anomalies if a.priority == AlertPriority.INFO]
        
        if critical:
            summary += f"🔴 *Critical:* {len(critical)}\n"
            for a in critical[:3]:  # Top 3
                summary += f"   • {a.ticker}: {a.anomaly_type.value}\n"
        
        if warning:
            summary += f"🟡 *Warning:* {len(warning)}\n"
            for a in warning[:3]:
                summary += f"   • {a.ticker}: {a.anomaly_type.value}\n"
        
        if info:
            summary += f"🟢 *Info:* {len(info)}\n"
        
        if not self.is_configured:
            print(summary)
            return True
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=summary.strip(),
                parse_mode=ParseMode.MARKDOWN
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send summary: {e}")
            return False
    
    async def test_connection_async(self) -> bool:
        """Test the Telegram bot connection"""
        if not self.is_configured:
            logger.warning("Telegram not configured")
            return False
        
        try:
            me = await self.bot.get_me()
            logger.info(f"Telegram bot connected: @{me.username}")
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="🤖 *Stock Anomaly Detector Connected!*\n\nYou will receive alerts when anomalies are detected.",
                parse_mode=ParseMode.MARKDOWN
            )
            return True
            
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
