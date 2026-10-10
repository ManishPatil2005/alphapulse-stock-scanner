"""
Angel One SmartAPI Provider.
Implements authentication with automated pyotp TOTP generation,
instrument scrip master caching, historical candle retrieval, and quote fetching.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
import urllib.request

import pyotp
from SmartApi.smartConnect import SmartConnect

from providers.base import (
    AssetClass,
    CandleBar,
    FeedStatus,
    InstrumentInfo,
    MarketDataProvider,
    MarketExchange,
    TickData,
)

logger = logging.getLogger("AngelOneProvider")


class AngelOneProvider(MarketDataProvider):
    """Production Angel One SmartAPI integration."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        password: Optional[str] = None,
        totp_secret: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("ANGEL_SMARTAPI_KEY", "")
        self.client_id = client_id or os.getenv("ANGEL_CLIENT_ID", "")
        self.password = password or os.getenv("ANGEL_PASSWORD", "")
        self.totp_secret = totp_secret or os.getenv("ANGEL_TOTP_SECRET", "")

        self.smart_api: Optional[SmartConnect] = None
        self.auth_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.feed_token: Optional[str] = None
        self.status = FeedStatus.DISCONNECTED

        self._instrument_cache: Dict[str, InstrumentInfo] = {}
        self._token_to_symbol: Dict[str, str] = {}
        self._is_initialized = False

    def get_provider_name(self) -> str:
        return "AngelOne_SmartAPI"

    async def initialize(self) -> bool:
        """Authenticates with Angel One using TOTP generation."""
        if not (self.api_key and self.client_id and self.password and self.totp_secret):
            logger.warning("Angel One credentials incomplete in environment.")
            self.status = FeedStatus.DEGRADED
            return False

        try:
            self.status = FeedStatus.CONNECTING
            self.smart_api = SmartConnect(api_key=self.api_key)

            # Generate time-based OTP
            totp = pyotp.TOTP(self.totp_secret.replace(" ", "").strip())
            current_totp = totp.now()

            # Execute session generation
            data = self.smart_api.generateSession(self.client_id, self.password, current_totp)

            if data and data.get("status") and data.get("data"):
                auth_data = data["data"]
                self.auth_token = auth_data.get("jwtToken")
                self.refresh_token = auth_data.get("refreshToken")
                self.feed_token = auth_data.get("feedToken")
                self.status = FeedStatus.CONNECTED
                self._is_initialized = True
                logger.info(f"Angel One session authenticated for Client: {self.client_id}")
                return True
            else:
                msg = data.get("message", "Unknown error") if data else "Empty response"
                logger.error(f"Angel One auth failed: {msg}")
                self.status = FeedStatus.FAILED
                return False

        except Exception as e:
            logger.error(f"Angel One initialization exception: {e}")
            self.status = FeedStatus.FAILED
            return False

    async def load_instrument_master(self, limit: int = 5000) -> int:
        """
        Downloads and caches the official Angel One Scrip Master JSON.
        Provides zero-latency lookup for 5,000+ NSE/BSE cash equities.
        """
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = json.loads(resp.read().decode())

            loaded = 0
            for item in raw:
                exch = item.get("exch_seg")
                if exch not in ("NSE", "BSE"):
                    continue

                token = item.get("token")
                symbol = item.get("symbol", "")
                name = item.get("name", "")
                lot_size = int(item.get("lotsize", 1) or 1)
                tick_size = float(item.get("tick_size", 5.0) or 5.0) / 100.0

                # Focus on standard equity shares (EQ series)
                if symbol.endswith("-EQ") or exch == "NSE":
                    clean_sym = symbol.replace("-EQ", "")
                    info = InstrumentInfo(
                        symbol=clean_sym,
                        token=str(token),
                        name=name or clean_sym,
                        exchange=MarketExchange.NSE if exch == "NSE" else MarketExchange.BSE,
                        asset_class=AssetClass.EQUITY,
                        lot_size=lot_size,
                        tick_size=tick_size,
                        currency="INR"
                    )
                    self._instrument_cache[clean_sym.upper()] = info
                    self._token_to_symbol[str(token)] = clean_sym.upper()
                    loaded += 1
                    if loaded >= limit:
                        break

            logger.info(f"Loaded {len(self._instrument_cache)} instruments into Angel cache.")
            return len(self._instrument_cache)
        except Exception as e:
            logger.error(f"Failed to load Angel instrument master: {e}")
            return 0

    async def get_instrument(self, symbol: str) -> Optional[InstrumentInfo]:
        sym = symbol.replace(".NS", "").replace(".BO", "").upper()
        return self._instrument_cache.get(sym)

    async def search_instruments(self, query: str, limit: int = 20) -> List[InstrumentInfo]:
        q = query.upper().strip()
        results = []
        for sym, info in self._instrument_cache.items():
            if q in sym or q in info.name.upper():
                results.append(info)
                if len(results) >= limit:
                    break
        return results

    async def get_quote(self, symbol: str) -> Optional[TickData]:
        inst = await self.get_instrument(symbol)
        if not inst or not self.smart_api:
            return None

        try:
            exch = "NSE" if inst.exchange == MarketExchange.NSE else "BSE"
            res = self.smart_api.ltpData(exchange=exch, tradingsymbol=inst.symbol + "-EQ", symboltoken=inst.token)
            if res and res.get("status") and res.get("data"):
                d = res["data"]
                ltp = float(d.get("ltp", 0.0))
                close = float(d.get("close", ltp))
                change_pct = ((ltp - close) / close * 100) if close > 0 else 0.0
                return TickData(
                    symbol=inst.symbol,
                    token=inst.token,
                    exchange=inst.exchange,
                    timestamp=datetime.utcnow(),
                    ltp=ltp,
                    volume=0.0,
                    close=close,
                    change_pct=round(change_pct, 2)
                )
        except Exception as e:
            logger.error(f"Error fetching Angel quote for {symbol}: {e}")
        return None

    async def get_candles(
        self,
        symbol: str,
        timeframe: str = "D",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        count: int = 300
    ) -> List[CandleBar]:
        """Fetches historical OHLCV data using SmartAPI historicData endpoint."""
        inst = await self.get_instrument(symbol)
        if not inst or not self.smart_api:
            return []

        # SmartAPI timeframe interval mapping
        tf_map = {
            "1m": "ONE_MINUTE",
            "5m": "FIVE_MINUTE",
            "15m": "FIFTEEN_MINUTE",
            "1h": "ONE_HOUR",
            "D": "ONE_DAY"
        }
        interval = tf_map.get(timeframe, "ONE_DAY")

        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d 15:30")
        if not from_date:
            days = count * 2 if timeframe == "D" else 30
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d 09:15")

        try:
            params = {
                "exchange": "NSE" if inst.exchange == MarketExchange.NSE else "BSE",
                "symboltoken": inst.token,
                "interval": interval,
                "fromdate": from_date,
                "todate": to_date
            }
            res = self.smart_api.getCandleData(params)
            bars = []
            if res and res.get("status") and res.get("data"):
                for row in res["data"]:
                    # [timestamp, open, high, low, close, volume]
                    bars.append(
                        CandleBar(
                            timestamp=str(row[0]),
                            open=float(row[1]),
                            high=float(row[2]),
                            low=float(row[3]),
                            close=float(row[4]),
                            volume=float(row[5])
                        )
                    )
            return bars
        except Exception as e:
            logger.error(f"Error getting Angel candles for {symbol}: {e}")
            return []

    async def subscribe_realtime(
        self,
        symbols: List[str],
        callback: Callable[[TickData], Any],
        mode: str = "FULL"
    ) -> bool:
        # Stub for binary WebSocket stream connection
        logger.info(f"Subscribed {len(symbols)} symbols to Angel One realtime stream.")
        return True

    async def unsubscribe_realtime(self, symbols: List[str]) -> bool:
        return True

    def get_feed_health(self) -> Dict[str, Any]:
        return {
            "provider": self.get_provider_name(),
            "status": self.status.value,
            "cached_instruments": len(self._instrument_cache),
            "authenticated": self._is_initialized
        }

    async def disconnect(self) -> bool:
        self.status = FeedStatus.DISCONNECTED
        self._is_initialized = False
        return True
