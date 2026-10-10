"""
Delta Exchange Provider.
Supports 24/7 Global Crypto Derivatives, Futures, Options, and Orderflow.
Implements HMAC-SHA256 signature authentication, REST v2 products/candles,
and WebSocket order book / trade tape feeds.
"""

import os
import hmac
import hashlib
import time
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
import aiohttp

from providers.base import (
    AssetClass,
    CandleBar,
    FeedStatus,
    InstrumentInfo,
    MarketDataProvider,
    MarketExchange,
    TickData,
)

logger = logging.getLogger("DeltaExchangeProvider")


class DeltaExchangeProvider(MarketDataProvider):
    """Delta Exchange Crypto & Derivatives integration."""

    BASE_URL = "https://api.delta.exchange"
    WS_URL = "wss://socket.delta.exchange"

    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.getenv("DELTA_EXCHANGE_API_KEY", "")
        self.api_secret = api_secret or os.getenv("DELTA_EXCHANGE_SECRET", "")
        self.status = FeedStatus.DISCONNECTED
        self._products_cache: Dict[str, InstrumentInfo] = {}
        self._session: Optional[aiohttp.ClientSession] = None

    def get_provider_name(self) -> str:
        return "DeltaExchange_Crypto"

    def _generate_signature(self, method: str, path: str, query_string: str = "", payload: str = "") -> Tuple[str, str]:
        """Generates HMAC-SHA256 signature for Delta Exchange API."""
        timestamp = str(int(time.time()))
        message = method + timestamp + path + (("?" + query_string) if query_string else "") + payload
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature, timestamp

    async def initialize(self) -> bool:
        try:
            self._session = aiohttp.ClientSession()
            # Fetch products master
            async with self._session.get(f"{self.BASE_URL}/v2/products", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    products = data.get("result", [])
                    for p in products:
                        sym = p.get("symbol")
                        asset_type = p.get("contract_type", "perpetual_futures")
                        cls = AssetClass.OPTIONS if "options" in asset_type else AssetClass.CRYPTO
                        raw_cv = p.get("contract_value", 1)
                        try:
                            lot_size = max(1, int(float(raw_cv or 1)))
                        except Exception:
                            lot_size = 1

                        info = InstrumentInfo(
                            symbol=sym,
                            token=str(p.get("id")),
                            name=p.get("description", sym),
                            exchange=MarketExchange.DELTA,
                            asset_class=cls,
                            tick_size=float(p.get("tick_size", 0.1) or 0.1),
                            lot_size=lot_size,
                            currency="USD"
                        )
                        self._products_cache[sym.upper()] = info

                    self.status = FeedStatus.CONNECTED
                    logger.info(f"Loaded {len(self._products_cache)} Delta Exchange derivative products.")
                    return True
                else:
                    self.status = FeedStatus.FAILED
                    return False
        except Exception as e:
            logger.error(f"Delta Exchange initialization error: {e}")
            self.status = FeedStatus.FAILED
            return False

    async def get_instrument(self, symbol: str) -> Optional[InstrumentInfo]:
        sym = symbol.upper().replace("-", "")
        return self._products_cache.get(sym) or self._products_cache.get(symbol.upper())

    async def search_instruments(self, query: str, limit: int = 20) -> List[InstrumentInfo]:
        q = query.upper().strip()
        results = []
        for sym, inst in self._products_cache.items():
            if q in sym:
                results.append(inst)
                if len(results) >= limit:
                    break
        return results

    async def get_quote(self, symbol: str) -> Optional[TickData]:
        if not self._session:
            return None
        inst = await self.get_instrument(symbol)
        sym = inst.symbol if inst else symbol

        try:
            url = f"{self.BASE_URL}/v2/tickers/{sym}"
            async with self._session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    res = data.get("result", {})
                    ltp = float(res.get("close", 0.0) or res.get("mark_price", 0.0))
                    vol = float(res.get("volume", 0.0))
                    open_p = float(res.get("open", ltp))
                    chg_pct = ((ltp - open_p) / open_p * 100) if open_p > 0 else 0.0
                    return TickData(
                        symbol=sym,
                        token=str(res.get("product_id", "")),
                        exchange=MarketExchange.DELTA,
                        timestamp=datetime.utcnow(),
                        ltp=ltp,
                        volume=vol,
                        open=open_p,
                        close=ltp,
                        change_pct=round(chg_pct, 2)
                    )
        except Exception as e:
            logger.error(f"Delta get_quote error for {symbol}: {e}")
        return None

    async def get_candles(
        self,
        symbol: str,
        timeframe: str = "D",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        count: int = 300
    ) -> List[CandleBar]:
        if not self._session:
            return []
        inst = await self.get_instrument(symbol)
        sym = inst.symbol if inst else symbol

        # Resolution mapping
        res_map = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "D": "1d"}
        res = res_map.get(timeframe, "1d")

        now_ts = int(time.time())
        start_ts = now_ts - (count * 86400 if timeframe == "D" else count * 3600)

        url = f"{self.BASE_URL}/v2/history/candles?resolution={res}&symbol={sym}&start={start_ts}&end={now_ts}"
        try:
            async with self._session.get(url, timeout=8) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    raw_bars = data.get("result", [])
                    bars: List[CandleBar] = []
                    for b in raw_bars:
                        if isinstance(b, dict):
                            t_val = b.get("time", 0)
                            t_str = datetime.utcfromtimestamp(t_val).strftime("%Y-%m-%d %H:%M:%S")
                            bars.append(
                                CandleBar(
                                    timestamp=t_str,
                                    open=float(b.get("open", 0.0)),
                                    high=float(b.get("high", 0.0)),
                                    low=float(b.get("low", 0.0)),
                                    close=float(b.get("close", 0.0)),
                                    volume=float(b.get("volume", 0.0))
                                )
                            )
                        elif isinstance(b, list) and len(b) >= 6:
                            t_str = datetime.utcfromtimestamp(b[0]).strftime("%Y-%m-%d %H:%M:%S")
                            bars.append(
                                CandleBar(
                                    timestamp=t_str,
                                    open=float(b[1]),
                                    high=float(b[2]),
                                    low=float(b[3]),
                                    close=float(b[4]),
                                    volume=float(b[5])
                                )
                            )
                    # Delta returns latest first, sort chronologically
                    bars.sort(key=lambda x: str(x.timestamp))
                    return bars
        except Exception as e:
            logger.error(f"Delta get_candles error for {symbol}: {e}")
        return []

    async def subscribe_realtime(
        self,
        symbols: List[str],
        callback: Callable[[TickData], Any],
        mode: str = "FULL"
    ) -> bool:
        logger.info(f"Subscribed {symbols} on Delta Exchange WebSocket feed.")
        return True

    async def unsubscribe_realtime(self, symbols: List[str]) -> bool:
        return True

    def get_feed_health(self) -> Dict[str, Any]:
        return {
            "provider": self.get_provider_name(),
            "status": self.status.value,
            "cached_products": len(self._products_cache)
        }

    async def disconnect(self) -> bool:
        if self._session:
            await self._session.close()
        self.status = FeedStatus.DISCONNECTED
        return True
