"""
scanner.py
Multithreaded Stock Scanner Engine:
Scans stock universes or custom lists against the core criteria:
1. Price is making Higher Highs (HH) and Higher Lows (HL)
2. RSI(21) is above 50
3. EMA (10, 20, 50) Compression (Coiling Squeeze)
4. Bullish Pinbar or Doji candle above EMAs
5. Exclude Upper / Lower Circuit Locked stocks
6. Episodic Pivots (Quarterly Earnings Catalyst Gap & Volume Surge)
7. Smart Money Concepts (ICT Liquidity Sweeps, FVGs, Market Profile)
"""

import time
import concurrent.futures
from typing import List, Dict, Any, Generator, Callable, Optional
from data_feed import get_stock_data
from technicals import analyze_market_structure
from stock_lists import UNIVERSES, STOCK_METADATA_MAP


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
    max_ema_spread_pct: float = 3.5,
    filter_circuits: bool = True,
    require_episodic_pivot: bool = False,
    require_liquidity_sweep: bool = False
) -> Dict[str, Any]:
    """
    Scans an individual stock ticker and evaluates:
    1. Higher Highs (HH) and Higher Lows (HL)
    2. RSI(21) > 50
    3. EMA (10, 20, 50) Compression
    4. Bullish Pinbar or Doji candle above EMAs
    5. Upper/Lower Circuit Lock detection
    6. Episodic Pivot catalyst gap
    7. SMC liquidity sweeps
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
            max_ema_spread_pct=max_ema_spread_pct,
            filter_circuits=filter_circuits,
            require_episodic_pivot=require_episodic_pivot,
            require_liquidity_sweep=require_liquidity_sweep
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

        # Fetch metadata from 5,000+ stock master universe
        meta_entry = STOCK_METADATA_MAP.get(symbol, {})
        company_name = meta_entry.get("name", symbol)
        sector = meta_entry.get("sector", "Equities")
        industry = meta_entry.get("industry", "Equity")
        market = meta_entry.get("market", meta.get("currency", "USD"))

        result = {
            "symbol": symbol,
            "company_name": company_name,
            "sector": sector,
            "industry": industry,
            "market": market,
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
    filter_circuits: bool = True,
    require_episodic_pivot: bool = False,
    require_liquidity_sweep: bool = False,
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
                max_ema_spread_pct,
                filter_circuits,
                require_episodic_pivot,
                require_liquidity_sweep
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
            "filter_circuits": filter_circuits,
            "require_episodic_pivot": require_episodic_pivot,
            "require_liquidity_sweep": require_liquidity_sweep,
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
    filter_circuits: bool = True,
    require_episodic_pivot: bool = False,
    require_liquidity_sweep: bool = False,
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
                max_ema_spread_pct,
                filter_circuits,
                require_episodic_pivot,
                require_liquidity_sweep
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

            meta_entry = STOCK_METADATA_MAP.get(sym, {})
            yield {
                "event": "progress",
                "scanned": scanned,
                "total": total,
                "current_symbol": sym,
                "is_match": is_match,
                "matches_count": len(matches),
                "stock": res if is_match else {
                    "symbol": sym,
                    "company_name": meta_entry.get("name", sym),
                    "sector": meta_entry.get("sector", "Equities"),
                    "industry": meta_entry.get("industry", "Equity"),
                    "price": res.get("price"),
                    "rsi_21": res.get("rsi_21"),
                    "is_circuit_locked": res.get("is_circuit_locked", False),
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
