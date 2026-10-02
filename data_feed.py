"""
data_feed.py
Enterprise-grade, high-speed market data provider designed for massive concurrent loads:
- Thread-safe in-memory caching with TTL
- Single-Flight Request Deduplication (prevents Thundering Herd problem)
- Dual-Engine Fallback: Direct Yahoo v8 Chart API + yfinance
- Automatic timestamp sanitization, deduplication, and monotonic sorting for Lightweight Charts
"""

import time
import json
import logging
import threading
import requests
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Connection-pooled HTTP session
_SESSION = requests.Session()
_ADAPTER = requests.adapters.HTTPAdapter(pool_connections=50, pool_maxsize=100, max_retries=2)
_SESSION.mount("https://", _ADAPTER)
_SESSION.mount("http://", _ADAPTER)
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
})

# In-memory cache & thread safety
_CACHE: Dict[Tuple[str, str, str], Tuple[float, pd.DataFrame, Dict[str, Any]]] = {}
_CACHE_LOCK = threading.Lock()
CACHE_TTL_SECONDS = 60.0  # 1 minute fresh cache

# Single-flight deduplication: (symbol, interval, range) -> threading.Event
_IN_FLIGHT: Dict[Tuple[str, str, str], threading.Event] = {}
_IN_FLIGHT_LOCK = threading.Lock()


def get_stock_data(
    symbol: str,
    interval: str = "1d",
    data_range: str = "6mo",
    use_cache: bool = True
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Fetches OHLCV historical candlestick data for a stock or index ticker.
    Thread-safe and protected against thundering herd when lakhs of users request data.
    """
    symbol = symbol.strip().upper()
    cache_key = (symbol, interval, data_range)
    now = time.time()

    # 1. Fast Cache Read
    if use_cache:
        with _CACHE_LOCK:
            if cache_key in _CACHE:
                cache_time, cached_df, cached_meta = _CACHE[cache_key]
                if now - cache_time < CACHE_TTL_SECONDS:
                    return cached_df.copy(), dict(cached_meta)

    # 2. Single-Flight Coalescing
    # If another thread is already fetching this exact symbol/timeframe, wait for it
    wait_event = None
    is_leader = False
    with _IN_FLIGHT_LOCK:
        if cache_key in _IN_FLIGHT:
            wait_event = _IN_FLIGHT[cache_key]
        else:
            wait_event = threading.Event()
            _IN_FLIGHT[cache_key] = wait_event
            is_leader = True

    if not is_leader and wait_event:
        # Wait up to 5 seconds for leader to finish
        wait_event.wait(timeout=5.0)
        with _CACHE_LOCK:
            if cache_key in _CACHE:
                _, cached_df, cached_meta = _CACHE[cache_key]
                return cached_df.copy(), dict(cached_meta)

    # 3. Leader fetches from upstream
    try:
        # Attempt 1: Direct Yahoo v8 API
        df, meta = _fetch_from_yahoo_v8(symbol, interval=interval, data_range=data_range)

        # Attempt 2: Fallback to yfinance if Direct API failed or returned empty
        if df is None or len(df) == 0:
            df, meta = _fetch_from_yfinance(symbol, interval=interval, data_range=data_range)

        if df is not None and len(df) > 0:
            # Guarantee strictly monotonic, duplicate-free data for charts
            df = df.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)

            with _CACHE_LOCK:
                _CACHE[cache_key] = (time.time(), df, meta)

            return df.copy(), meta

        return None, {"symbol": symbol, "error": "Unable to fetch market data"}

    finally:
        # Release in-flight lock for other threads
        if is_leader:
            with _IN_FLIGHT_LOCK:
                if cache_key in _IN_FLIGHT:
                    ev = _IN_FLIGHT.pop(cache_key)
                    ev.set()


def _fetch_from_yahoo_v8(
    symbol: str,
    interval: str = "1d",
    data_range: str = "6mo"
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """Direct high-speed query to Yahoo Finance chart API."""
    url = f"https://query2.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(symbol)}"
    params = {
        "range": data_range,
        "interval": interval,
        "includePrePost": "false",
        "events": "div|split"
    }

    try:
        resp = _SESSION.get(url, params=params, timeout=6)
        if resp.status_code != 200:
            return None, {}

        data = resp.json()
        chart = data.get("chart", {})
        results = chart.get("result")
        if not results:
            return None, {}

        item = results[0]
        meta = item.get("meta", {})
        timestamps = item.get("timestamp", [])
        indicators = item.get("indicators", {}).get("quote", [{}])[0]

        if not timestamps or not indicators:
            return None, meta

        opens = indicators.get("open", [])
        highs = indicators.get("high", [])
        lows = indicators.get("low", [])
        closes = indicators.get("close", [])
        volumes = indicators.get("volume", [])

        records = []
        for i in range(len(timestamps)):
            ts = timestamps[i]
            o = opens[i] if i < len(opens) else None
            h = highs[i] if i < len(highs) else None
            l = lows[i] if i < len(lows) else None
            c = closes[i] if i < len(closes) else None
            v = volumes[i] if i < len(volumes) else 0

            # Filter out null / holiday candles
            if o is not None and h is not None and l is not None and c is not None:
                records.append({
                    "time": int(ts),
                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "volume": float(v) if v is not None else 0.0
                })

        if not records:
            return None, meta

        df = pd.DataFrame(records)
        meta_dict = {
            "symbol": symbol,
            "currency": meta.get("currency", "INR" if symbol.endswith(".NS") else "USD"),
            "exchange": meta.get("exchangeName", "NSE" if symbol.endswith(".NS") else "US"),
            "instrumentType": meta.get("instrumentType", "EQUITY"),
            "shortName": meta.get("shortName", symbol),
            "regularMarketPrice": meta.get("regularMarketPrice", records[-1]["close"]),
            "chartPreviousClose": meta.get("chartPreviousClose", records[0]["close"])
        }
        return df, meta_dict

    except Exception as e:
        logger.warning(f"Yahoo v8 fetch failed for {symbol}: {e}")
        return None, {}


def _fetch_from_yfinance(
    symbol: str,
    interval: str = "1d",
    data_range: str = "6mo"
) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """Fallback fetcher using yfinance."""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df_raw = ticker.history(period=data_range, interval=interval, auto_adjust=True)

        if df_raw.empty:
            return None, {}

        df_raw = df_raw.reset_index()
        date_col = "Date" if "Date" in df_raw.columns else "Datetime"
        if date_col not in df_raw.columns:
            return None, {}

        df_raw["time"] = df_raw[date_col].astype("int64") // 10**9

        df = pd.DataFrame({
            "time": df_raw["time"],
            "open": df_raw["Open"],
            "high": df_raw["High"],
            "low": df_raw["Low"],
            "close": df_raw["Close"],
            "volume": df_raw["Volume"]
        }).dropna()

        meta_dict = {
            "symbol": symbol,
            "currency": "INR" if symbol.endswith(".NS") else "USD",
            "exchange": "NSE" if symbol.endswith(".NS") else "US",
            "regularMarketPrice": float(df["close"].iloc[-1]) if len(df) > 0 else 0.0
        }
        return df, meta_dict

    except Exception as e:
        logger.warning(f"yfinance fallback failed for {symbol}: {e}")
        return None, {}
