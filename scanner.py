"""
scanner.py
Multithreaded Stock Scanner Engine:
Scans stock universes or custom lists against the core criteria:
1. Price is making Higher Highs (HH) and Higher Lows (HL)
2. RSI(21) is above 50
"""

import time
import concurrent.futures
from typing import List, Dict, Any, Generator, Callable, Optional
from data_feed import get_stock_data
from technicals import analyze_market_structure
from stock_lists import UNIVERSES


def scan_single_stock(
    symbol: str,
    timeframe: str = "1d",
    data_range: str = "6mo",
    rsi_period: int = 21,
    rsi_threshold: float = 50.0,
    swing_window: int = 3,
    min_volume: float = 0,
    require_hh_hl: bool = True,
    require_rsi: bool = True,
    require_ema_compression: bool = False,
    require_pinbar_doji: bool = False,
    max_ema_spread_pct: float = 3.5
) -> Dict[str, Any]:
    """
    Scans an individual stock ticker and evaluates:
    1. Higher Highs (HH) and Higher Lows (HL)
    2. RSI(21) > 50
    3. EMA (10, 20, 50) Compression
    4. Bullish Pinbar or Doji candle above EMAs
    """
    symbol = symbol.strip().upper()
    try:
        df, meta = get_stock_data(symbol, interval=timeframe, data_range=data_range)
        if df is None or len(df) == 0:
            return {
                "symbol": symbol,
                "status": "error",
                "passes_scan": False,
                "message": "No price data returned"
            }

        analysis = analyze_market_structure(
            df,
            rsi_period=rsi_period,
            rsi_threshold=rsi_threshold,
            swing_window=swing_window,
            require_hh_hl=require_hh_hl,
            require_rsi=require_rsi,
            require_ema_compression=require_ema_compression,
            require_pinbar_doji=require_pinbar_doji,
            max_ema_spread_pct=max_ema_spread_pct
        )

        if not analysis.get("is_valid", False):
            return {
                "symbol": symbol,
                "status": "error",
                "passes_scan": False,
                "message": analysis.get("error", "Invalid data")
            }

        # Apply optional volume filter if requested
        if min_volume > 0 and analysis.get("volume", 0) < min_volume:
            analysis["passes_scan"] = False
            analysis["volume_filter_failed"] = True

        result = {
            "symbol": symbol,
            "currency": meta.get("currency", "USD"),
            "status": "success",
            **analysis
        }
        return result

    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "passes_scan": False,
            "message": str(e)
        }


def run_batch_scan(
    symbols: List[str],
    timeframe: str = "1d",
    data_range: str = "6mo",
    rsi_period: int = 21,
    rsi_threshold: float = 50.0,
    swing_window: int = 3,
    min_volume: float = 0,
    require_hh_hl: bool = True,
    require_rsi: bool = True,
    require_ema_compression: bool = False,
    require_pinbar_doji: bool = False,
    max_ema_spread_pct: float = 3.5,
    max_workers: int = 10,
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """
    Scans a list of symbols in parallel with thread pool execution.
    """
    total = len(symbols)
    scanned = 0
    matches = []
    all_results = []
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(
                scan_single_stock,
                sym,
                timeframe,
                data_range,
                rsi_period,
                rsi_threshold,
                swing_window,
                min_volume,
                require_hh_hl,
                require_rsi,
                require_ema_compression,
                require_pinbar_doji,
                max_ema_spread_pct
            ): sym
            for sym in symbols
        }

        for future in concurrent.futures.as_completed(future_to_symbol):
            sym = future_to_symbol[future]
            try:
                res = future.result()
            except Exception as e:
                res = {
                    "symbol": sym,
                    "status": "error",
                    "passes_scan": False,
                    "message": str(e)
                }

            scanned += 1
            all_results.append(res)
            if res.get("passes_scan"):
                matches.append(res)

            if progress_callback:
                progress_callback({
                    "type": "progress",
                    "scanned": scanned,
                    "total": total,
                    "current_symbol": sym,
                    "passes_scan": res.get("passes_scan", False),
                    "matches_count": len(matches),
                    "latest_result": res if res.get("passes_scan") else None
                })

    elapsed = round(time.time() - start_time, 2)

    # Sort matches by RSI descending or change percentage
    matches.sort(key=lambda x: x.get("rsi_21", 0), reverse=True)

    return {
        "total_scanned": total,
        "matches_count": len(matches),
        "elapsed_seconds": elapsed,
        "criteria": {
            "condition_1": "Price is making Higher Highs (HH) and Higher Lows (HL)",
            "condition_2": f"RSI({rsi_period}) > {rsi_threshold}",
            "condition_3": f"EMA (10, 20, 50) Compression <= {max_ema_spread_pct}%",
            "condition_4": "Bullish Pinbar or Doji above EMAs",
            "timeframe": timeframe,
            "swing_window": swing_window
        },
        "matches": matches,
        "all_results": all_results
    }


def stream_scan(
    symbols: List[str],
    timeframe: str = "1d",
    data_range: str = "6mo",
    rsi_period: int = 21,
    rsi_threshold: float = 50.0,
    swing_window: int = 3,
    min_volume: float = 0,
    require_hh_hl: bool = True,
    require_rsi: bool = True,
    require_ema_compression: bool = False,
    require_pinbar_doji: bool = False,
    max_ema_spread_pct: float = 3.5,
    max_workers: int = 8
) -> Generator[Dict[str, Any], None, None]:
    """
    Generator yielding live scan progress and match events for Server-Sent Events (SSE).
    """
    total = len(symbols)
    scanned = 0
    matches = []
    start_time = time.time()

    yield {
        "event": "start",
        "total": total,
        "timeframe": timeframe
    }

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {
            executor.submit(
                scan_single_stock,
                sym,
                timeframe,
                data_range,
                rsi_period,
                rsi_threshold,
                swing_window,
                min_volume,
                require_hh_hl,
                require_rsi,
                require_ema_compression,
                require_pinbar_doji,
                max_ema_spread_pct
            ): sym
            for sym in symbols
        }

        for future in concurrent.futures.as_completed(future_to_symbol):
            sym = future_to_symbol[future]
            try:
                res = future.result()
            except Exception as e:
                res = {
                    "symbol": sym,
                    "status": "error",
                    "passes_scan": False,
                    "message": str(e)
                }

            scanned += 1
            is_match = res.get("passes_scan", False)
            if is_match:
                matches.append(res)

            yield {
                "event": "progress",
                "scanned": scanned,
                "total": total,
                "current_symbol": sym,
                "is_match": is_match,
                "matches_count": len(matches),
                "stock": res if is_match else {
                    "symbol": sym,
                    "price": res.get("price"),
                    "rsi_21": res.get("rsi_21"),
                    "passes_scan": False
                }
            }

    elapsed = round(time.time() - start_time, 2)
    matches.sort(key=lambda x: x.get("rsi_21", 0), reverse=True)

    yield {
        "event": "complete",
        "total": total,
        "matches_count": len(matches),
        "elapsed_seconds": elapsed,
        "matches": matches
    }
