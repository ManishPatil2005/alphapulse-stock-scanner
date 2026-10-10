"""
Unified Market Data Manager.
Orchestrates primary, secondary, and failover providers.
Routes Indian Equities/F&O to Angel One, Crypto/Derivatives to Delta Exchange,
and fallback requests to synthetic offline cache.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
from providers.base import CandleBar, InstrumentInfo, MarketDataProvider, TickData
from providers.angel_one import AngelOneProvider
from providers.delta_exchange import DeltaExchangeProvider
from services.normalizer import PriceNormalizer
from services.feed_health import FeedHealthEngine

logger = logging.getLogger("UnifiedDataManager")


class UnifiedDataManager:
    """Institutional Market Data Hub & Provider Router."""

    def __init__(self):
        self.angel_provider = AngelOneProvider()
        self.delta_provider = DeltaExchangeProvider()
        self.feed_health = FeedHealthEngine()
        self._is_initialized = False

    async def initialize(self):
        """Initializes all registered feeds and registers them with health engine."""
        if self._is_initialized:
            return

        # Register feed monitors
        self.feed_health.register_feed(self.angel_provider.get_provider_name())
        self.feed_health.register_feed(self.delta_provider.get_provider_name())

        # Initialize providers concurrently
        logger.info("Initializing Angel One provider...")
        angel_ok = await self.angel_provider.initialize()
        if angel_ok:
            await self.angel_provider.load_instrument_master(limit=5000)

        logger.info("Initializing Delta Exchange provider...")
        delta_ok = await self.delta_provider.initialize()

        await self.feed_health.start()
        self._is_initialized = True
        logger.info("Unified Data Manager initialized.")

    def _select_provider(self, symbol: str) -> MarketDataProvider:
        """Routes symbol to appropriate market provider based on symbol patterns."""
        sym = symbol.upper()
        # Crypto or derivative pairs
        if any(term in sym for term in ("USDT", "BTC", "ETH", "SOL", "XRP", "PERP")):
            return self.delta_provider
        # Indian equities and default
        return self.angel_provider

    async def get_chart_data(
        self,
        symbol: str,
        timeframe: str = "D",
        count: int = 250
    ) -> Tuple[List[CandleBar], Dict[str, Any]]:
        """
        Fetches, validates, and normalizes candlestick data with zero scale distortion.
        Fixes Issue 1 (Rs 12000 showing as 120 or 4).
        """
        provider = self._select_provider(symbol)
        raw_candles = await provider.get_candles(symbol, timeframe=timeframe, count=count)

        inst = await provider.get_instrument(symbol)
        clean_candles, diagnostics = PriceNormalizer.validate_and_normalize_candles(raw_candles, inst)

        currency, precision = PriceNormalizer.get_currency_and_precision(symbol)
        diagnostics["currency"] = currency
        diagnostics["precision"] = precision
        diagnostics["provider"] = provider.get_provider_name()

        return clean_candles, diagnostics

    async def get_quote(self, symbol: str) -> Optional[TickData]:
        provider = self._select_provider(symbol)
        tick = await provider.get_quote(symbol)
        if tick:
            self.feed_health.record_tick(provider.get_provider_name(), tick.timestamp)
        return tick

    async def search(self, query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Aggregated cross-asset symbol search."""
        results = []
        # Search Angel instruments
        angel_matches = await self.angel_provider.search_instruments(query, limit=limit)
        for m in angel_matches:
            results.append({
                "symbol": m.symbol,
                "name": m.name,
                "exchange": m.exchange.value,
                "asset_class": m.asset_class.value,
                "currency": m.currency
            })

        # Search Delta products
        delta_matches = await self.delta_provider.search_instruments(query, limit=limit)
        for m in delta_matches:
            results.append({
                "symbol": m.symbol,
                "name": m.name,
                "exchange": m.exchange.value,
                "asset_class": m.asset_class.value,
                "currency": m.currency
            })

        return results[:limit]

    def get_system_health(self) -> Dict[str, Any]:
        """Returns comprehensive feed health dashboard status."""
        return self.feed_health.get_summary()
