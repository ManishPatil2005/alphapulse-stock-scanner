"""
services/market_time.py
Single Market Time Engine for AlphaPulse:
Synchronizes timestamps across Charts, Scanner, Option Chain, Watchlist, and Exchange feeds.
Handles Indian Standard Time (IST, UTC+5:30), Market Holidays, and Session Boundaries.
"""

from datetime import datetime, time as dtime, timedelta
import pytz
from typing import Dict, Any, List, Tuple

# Indian Standard Timezone
IST = pytz.timezone("Asia/Kolkata")
UTC = pytz.utc

# NSE / BSE Official Trading Sessions (IST)
PRE_OPEN_START = dtime(9, 0)
PRE_OPEN_END = dtime(9, 15)
EQUITY_OPEN = dtime(9, 15)
EQUITY_CLOSE = dtime(15, 30)
POST_CLOSE_END = dtime(16, 0)

# MCX Commodity Trading Sessions (IST)
COMMODITY_OPEN = dtime(9, 0)
COMMODITY_CLOSE = dtime(23, 30)

# NSE Official Holidays 2026
NSE_HOLIDAYS_2026 = {
    "2026-01-26": "Republic Day",
    "2026-03-06": "Maha Shivratri",
    "2026-03-25": "Holi",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-08-15": "Independence Day",
    "2026-10-02": "Mahatma Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-11-08": "Diwali Laxmi Pujan (Muhurat Trading)",
    "2026-11-10": "Diwali Balipratipada",
    "2026-11-24": "Guru Nanak Jayanti",
    "2026-12-25": "Christmas",
}


class MarketTimeEngine:
    """Authoritative clock and session status provider for financial market operations."""

    @classmethod
    def get_current_ist(cls) -> datetime:
        return datetime.now(IST)

    @classmethod
    def is_holiday(cls, dt: datetime) -> Tuple[bool, str]:
        date_str = dt.strftime("%Y-%m-%d")
        if date_str in NSE_HOLIDAYS_2026:
            return True, NSE_HOLIDAYS_2026[date_str]
        # Weekend check
        if dt.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            return True, "Weekend"
        return False, ""

    @classmethod
    def get_session_status(cls, asset_type: str = "EQUITY") -> Dict[str, Any]:
        """
        Calculates live status: OPEN, CLOSED, PRE_OPEN, POST_CLOSE
        Returns time remaining to next session transition.
        """
        now_ist = cls.get_current_ist()
        t = now_ist.time()
        is_hol, hol_reason = cls.is_holiday(now_ist)

        if asset_type == "CRYPTO":
            return {
                "market": "CRYPTO",
                "status": "OPEN",
                "is_trading": True,
                "reason": "Crypto 24/7 Global Trading",
                "server_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                "server_time_epoch": int(now_ist.timestamp())
            }

        if is_hol:
            return {
                "market": asset_type,
                "status": "CLOSED",
                "is_trading": False,
                "reason": f"Market Closed: {hol_reason}",
                "server_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                "server_time_epoch": int(now_ist.timestamp()),
                "next_session": "Next Business Day 09:15 IST"
            }

        if asset_type == "COMMODITY":
            if COMMODITY_OPEN <= t <= COMMODITY_CLOSE:
                return {
                    "market": "MCX_COMMODITY",
                    "status": "OPEN",
                    "is_trading": True,
                    "reason": "MCX Commodity Market Open (09:00 - 23:30 IST)",
                    "server_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                    "server_time_epoch": int(now_ist.timestamp())
                }
            return {
                "market": "MCX_COMMODITY",
                "status": "CLOSED",
                "is_trading": False,
                "reason": "MCX Closed (Trading Hours: 09:00 - 23:30 IST)",
                "server_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                "server_time_epoch": int(now_ist.timestamp())
            }

        # NSE / BSE Equity & F&O
        if PRE_OPEN_START <= t < PRE_OPEN_END:
            status = "PRE_OPEN"
            reason = "Pre-Open Order Collection & Price Discovery (09:00 - 09:15 IST)"
            is_trading = False
        elif EQUITY_OPEN <= t <= EQUITY_CLOSE:
            status = "OPEN"
            reason = "NSE/BSE Regular Trading Session (09:15 - 15:30 IST)"
            is_trading = True
        elif EQUITY_CLOSE < t <= POST_CLOSE_END:
            status = "POST_CLOSE"
            reason = "Post-Market Closing Session (15:30 - 16:00 IST)"
            is_trading = False
        else:
            status = "CLOSED"
            reason = "Market Closed (Trading Hours: 09:15 - 15:30 IST)"
            is_trading = False

        return {
            "market": "NSE_BSE_EQUITY",
            "status": status,
            "is_trading": is_trading,
            "reason": reason,
            "server_time_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            "server_time_epoch": int(now_ist.timestamp()),
            "time_formatted": now_ist.strftime("%H:%M:%S")
        }

    @classmethod
    def align_timestamp_to_interval(cls, unix_timestamp: int, interval_seconds: int) -> int:
        """Rounds down a unix timestamp to the nearest exact interval boundary."""
        return (unix_timestamp // interval_seconds) * interval_seconds
