"""
Unified Provider Abstraction Layer for Market Data Feeds.
Designed from first principles to ensure zero architecture change when swapping
or chaining providers (Angel One, Delta Exchange, Zerodha, Upstox, Dhan, IBKR, Binance).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    INDEX = "INDEX"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    COMMODITY = "COMMODITY"


class MarketExchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"
    NFO = "NFO"
    BFO = "BFO"
    CDS = "CDS"
    MCX = "MCX"
    DELTA = "DELTA"
    BINANCE = "BINANCE"
    US = "US"


class FeedStatus(str, Enum):
    CONNECTED = "CONNECTED"
    CONNECTING = "CONNECTING"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"
    FAILED = "FAILED"
    DEGRADED = "DEGRADED"


@dataclass
class InstrumentInfo:
    symbol: str
    token: str
    name: str
    exchange: MarketExchange
    asset_class: AssetClass
    lot_size: int = 1
    tick_size: float = 0.05
    strike: float = 0.0
    expiry: Optional[str] = None
    instrument_type: Optional[str] = None
    currency: str = "INR"
    sector: Optional[str] = None
    industry: Optional[str] = None


@dataclass
class CandleBar:
    timestamp: str  # ISO 8601 or YYYY-MM-DD HH:MM:SS
    open: float
    high: float
    low: float
    close: float
    volume: float
    trades: Optional[int] = None
    vwap: Optional[float] = None


@dataclass
class TickData:
    symbol: str
    token: str
    exchange: MarketExchange
    timestamp: datetime
    ltp: float
    volume: float
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    change_pct: float = 0.0
    best_bid: float = 0.0
    best_bid_qty: float = 0.0
    best_ask: float = 0.0
    best_ask_qty: float = 0.0
    total_buy_qty: float = 0.0
    total_sell_qty: float = 0.0
    open_interest: float = 0.0
    last_trade_time: Optional[datetime] = None


@dataclass
class OrderBookLevel:
    price: float
    quantity: float
    orders_count: int = 1


@dataclass
class OrderBookSnapshot:
    symbol: str
    timestamp: datetime
    bids: List[OrderBookLevel] = field(default_factory=list)
    asks: List[OrderBookLevel] = field(default_factory=list)


class MarketDataProvider(ABC):
    """Abstract base class for all plug-and-play market data providers."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Unique identifier for this provider."""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """Authenticate and prepare provider connection."""
        pass

    @abstractmethod
    async def get_instrument(self, symbol: str) -> Optional[InstrumentInfo]:
        """Fetch verified instrument specification."""
        pass

    @abstractmethod
    async def search_instruments(self, query: str, limit: int = 20) -> List[InstrumentInfo]:
        """Search instruments matching user query."""
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> Optional[TickData]:
        """Fetch current quote with best bid/ask snapshot."""
        pass

    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str = "D",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        count: int = 300
    ) -> List[CandleBar]:
        """Fetch historical candlestick series."""
        pass

    @abstractmethod
    async def subscribe_realtime(
        self,
        symbols: List[str],
        callback: Callable[[TickData], Any],
        mode: str = "FULL"
    ) -> bool:
        """Subscribe to real-time tick streaming."""
        pass

    @abstractmethod
    async def unsubscribe_realtime(self, symbols: List[str]) -> bool:
        """Unsubscribe from streaming updates."""
        pass

    @abstractmethod
    def get_feed_health(self) -> Dict[str, Any]:
        """Return diagnostic heartbeat, latency, and connection status."""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Gracefully disconnect sockets and release resources."""
        pass
