# Data Provider Layer Specification

## 1. Overview
The Data Provider Layer abstracts all external market data sources, providing a unified, normalized interface to the platform's analytical engines. It employs the Adapter design pattern to enable plug-and-play integration of multiple brokers and data vendors.

## 2. Design Pattern & Interfaces
All data providers must implement the following base interfaces, designed as Python Abstract Base Classes (ABCs).

### 2.1 Abstract Base Classes

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Optional
from datetime import datetime
import pandas as pd

class MarketDataProvider(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> Dict:
        """Fetch the latest L1 quote for a symbol."""
        pass
        
    @abstractmethod
    def get_instruments(self, exchange: str) -> pd.DataFrame:
        """Fetch master list of instruments."""
        pass

    @abstractmethod
    def search_symbols(self, query: str) -> List[Dict]:
        """Search for instruments matching a query string."""
        pass

class HistoricalDataProvider(ABC):
    @abstractmethod
    def get_candles(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch historical OHLCV candles."""
        pass
        
    @abstractmethod
    def get_ticks(self, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
        """Fetch historical tick data (L1 trades/quotes)."""
        pass

class RealtimeDataProvider(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to real-time feed."""
        pass
        
    @abstractmethod
    def subscribe(self, symbols: List[str], channels: List[str]) -> bool:
        """Subscribe to specific streams for given symbols."""
        pass
        
    @abstractmethod
    def on_tick(self, callback: Callable[[Dict], None]) -> None:
        """Register callback for tick (trade) updates."""
        pass
        
    @abstractmethod
    def on_depth(self, callback: Callable[[Dict], None]) -> None:
        """Register callback for L2/L3 order book depth updates."""
        pass
        
    @abstractmethod
    def disconnect(self) -> bool:
        """Gracefully disconnect from the feed."""
        pass

class OrderflowProvider(ABC):
    @abstractmethod
    def get_order_book(self, symbol: str, depth: int) -> Dict:
        """Get current limit order book snapshot up to 'depth' levels."""
        pass
        
    @abstractmethod
    def get_trade_tape(self, symbol: str) -> List[Dict]:
        """Get recent continuous trades."""
        pass
        
    @abstractmethod
    def stream_trades(self, symbol: str) -> None:
        """Subscribe to real-time trade execution tape."""
        pass

class NewsProvider(ABC):
    @abstractmethod
    def get_news(self, symbol: str) -> List[Dict]:
        pass
    
    @abstractmethod
    def stream_news(self) -> None:
        pass

class CorporateActionProvider(ABC):
    @abstractmethod
    def get_earnings(self, symbol: str) -> List[Dict]:
        pass
        
    @abstractmethod
    def get_dividends(self, symbol: str) -> List[Dict]:
        pass
        
    @abstractmethod
    def get_splits(self, symbol: str) -> List[Dict]:
        pass
```

## 3. Angel One SmartAPI Integration Spec
- **Authentication Flow:** `client_id` + `password` + `TOTP` -> returns JWT token -> refresh token rotation mechanism for long-lived sessions.
- **REST Endpoints:**
  - Login: `/rest/secure/angelbroking/user/v1/loginByPassword`
  - Historical Data: `/rest/secure/angelbroking/historical/v1/getCandleData`
- **WebSocket Binary Feed:**
  - URL: `wss://smartapiws.angelbroking.com/smart-stream`
  - Modes: LTP (Last Traded Price), Quote (L1), SnapQuote (L2 depth up to 5 levels).
- **Instrument Master:** Daily CSV/JSON download from `https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json`.
- **Rate Limits:** 10 requests/second for REST, max 3 concurrent WebSocket connections.
- **Error Handling:** Auto-renew token on token expiry/401, handle exchange market hours gently, monitor API circuit limits.

## 4. Delta Exchange Integration Spec
- **Authentication:** API key + HMAC-SHA256 signed requests on headers.
- **REST v2:** `/v2/products`, `/v2/history/candles`, `/v2/l2orderbook`
- **WebSocket:** `wss://socket.delta.exchange`, subscribing to channels: `v2/ticker`, `candlestick`, `l2_orderbook`, `all_trades`.
- **Instruments:** Supports BTC, ETH perpetual swaps, traditional futures, options chains, and MOVE contracts.

## 5. Feed Health Engine
- **Heartbeat System:** 5-second ping/pong protocol to detect stale connections.
- **Auto-Reconnect:** Exponential backoff strategy (1s, 2s, 4s, 8s, up to max 30s).
- **Failover:** Primary Feed -> Secondary Backup -> Cached Replay (for UI recovery).
- **Latency Tracking:** Rolling calculation of p50, p95, p99 latency per feed.
- **Dashboard:** Visual feed status dashboard exposing latency metrics and connection states.

## 6. Price Normalization & Validation
- **Verification:** Confirm exchange segment (e.g., NSE_CM vs NSE_FO), lot size, tick size, and price precision before rendering.
- **OHLCV Sanity:** 
  - `Low <= Open <= High` and `Low <= Close <= High`
  - `Volume >= 0`
  - Timestamps strictly monotonically increasing.
- **Currency Detection:** INR for .NS/.BO, USD for US stocks, BTC/USDT for crypto.

## 7. Migration Plan from YFinance
- **Phase 1:** Dual-run YFinance and institutional feeds (Angel One for Indian equities) in shadow mode.
- **Phase 2:** Redirect Real-time chart subscriptions to WebSocket feeds; keep YFinance for backfill.
- **Phase 3:** Total cutover for historical data using institutional REST APIs; deprecate YFinance entirely to avoid rate-limit bans and delayed quotes.

## 8. Future Provider Stubs
- Zerodha (KiteConnect)
- Upstox API
- Dhan API
- Interactive Brokers (IBKR TWS API)
- Polygon.io (US Equities/Options)
- Binance (Crypto)
- CQG & Rithmic (Futures & Orderflow)
