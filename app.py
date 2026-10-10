"""
app.py
Enterprise-Grade Trading Application & Stock Scanner Backend:
- Scalable architecture designed for high concurrent user loads (lakhs of users)
- In-memory shared scan cache & GZip compression
- 5,000+ Cash Equities (NSE/US) with Sector & Industry classification
- Backtesting Engine (Win Rate %, Profit Factor, Max Drawdown %, Equity Curve, Trade Logs)
- Circuit Filter (Upper/Lower Circuit locks detection)
- Episodic Pivots Scanner (Catalyst Gap-Up + Volume Surge)
- Smart Money Concepts (ICT Liquidity Sweeps, FVGs, Market Profile POC/VAH/VAL)
- In-Trade Psychology & Risk Management
- REST & Server-Sent Events (SSE) endpoints for live scanner streaming and charting
"""

import json
import time
import asyncio
import threading
from typing import Optional, List, Dict, Any, Tuple
from fastapi import FastAPI, Query, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from datetime import datetime

from auth.security import get_current_user, require_roles, Role

from stock_lists import UNIVERSES, SECTOR_MAP, STOCK_METADATA_MAP
from data_feed import get_stock_data
from technicals import analyze_market_structure
from scanner import run_batch_scan, stream_scan, scan_single_stock
from ticker_search import search_tickers
from backtester import run_strategy_backtest

app = FastAPI(
    title="AlphaPulse Stock Scanner & Trading Terminal",
    description="Enterprise-grade Stock Scanner for Higher Highs/Lows, RSI(21) > 50, Episodic Pivots, SMC & Backtesting",
    version="2.1.0"
)

# Enable GZip compression (reduces payload by ~80% for candlestick data)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Base directory for absolute asset resolution (required for Vercel serverless deployment)
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent

# Static and template setup
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Shared In-Memory Scan Cache: key -> (timestamp, results_dict)
_GLOBAL_SCAN_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_SCAN_CACHE_TTL = 120.0  # 2 minutes cache for scans
_SCAN_LOCK = threading.Lock()


class ScanRequest(BaseModel):
    universe: str = "us_mega_caps"
    custom_symbols: Optional[str] = None
    timeframe: str = "1d"
    rsi_period: int = 21
    rsi_threshold: float = 50.0
    swing_window: int = 3
    min_volume: float = 0
    require_hh_hl: bool = True
    require_rsi: bool = True
    require_ema_compression: bool = False
    require_pinbar_doji: bool = False
    max_ema_spread_pct: float = 3.5
    filter_circuits: bool = True
    require_episodic_pivot: bool = False
    require_liquidity_sweep: bool = False
    sector: Optional[str] = None


class BacktestRequest(BaseModel):
    symbol: str = "NVDA"
    timeframe: str = "1d"
    data_range: str = "1y"
    strategy: str = "master"
    risk_reward: float = 2.0
    initial_capital: float = 100000.0
    risk_per_trade_pct: float = 1.0


def load_default_nvda():
    try:
        with open(BASE_DIR / "default_nvda.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


@app.get("/", response_class=HTMLResponse)
@app.get("/app.py", response_class=HTMLResponse)
@app.get("/api/index.py", response_class=HTMLResponse)
@app.get("/api", response_class=HTMLResponse)
@app.get("/index", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Serves the main trading application dashboard with pre-loaded initial chart."""
    initial_data = load_default_nvda()
    context = {
        "request": request,
        "universes": UNIVERSES,
        "sectors": sorted(list(SECTOR_MAP.keys())),
        "initial_data": initial_data
    }
    try:
        # Modern Starlette 0.36+ (used by Vercel)
        response = templates.TemplateResponse(request=request, name="index.html", context=context)
    except TypeError:
        # Legacy Starlette fallback
        response = templates.TemplateResponse("index.html", context)

    # Force browsers and edge proxies to always fetch fresh version (prevent stale script cache)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.get("/api/search")
async def search_endpoint(q: str = Query("", description="Symbol or company name prefix")):
    """
    Instant search suggestions endpoint (<1ms).
    Searches across US stocks, Indian NSE/BSE stocks, and major indices.
    """
    results = search_tickers(q, limit=12)
    return {"query": q, "results": results}


@app.get("/api/universes")
async def get_universes():
    """Returns list of stock universes."""
    return {
        "universes": [
            {
                "id": k,
                "name": v["name"],
                "market": v["market"],
                "count": len(v["symbols"])
            }
            for k, v in UNIVERSES.items()
        ]
    }


@app.get("/api/sectors")
async def get_sectors():
    """Returns all available market sectors with stock counts from 5,000+ universe."""
    return {
        "sectors": [
            {
                "name": sec,
                "count": len(syms)
            }
            for sec, syms in sorted(SECTOR_MAP.items())
        ]
    }


@app.post("/api/scan")
async def execute_scan(req: ScanRequest):
    """
    Executes a scan or returns instantly from the high-speed shared memory cache.
    Protects upstream data feeds when lakhs of users scan simultaneously.
    """
    cache_key = (
        f"{req.universe}_{req.timeframe}_{req.rsi_period}_{req.rsi_threshold}_"
        f"{req.swing_window}_{req.require_hh_hl}_{req.require_rsi}_{req.require_ema_compression}_"
        f"{req.require_pinbar_doji}_{req.max_ema_spread_pct}_{req.filter_circuits}_"
        f"{req.require_episodic_pivot}_{req.require_liquidity_sweep}_{req.sector}"
    )
    now = time.time()

    # Fast in-memory read
    with _SCAN_LOCK:
        if cache_key in _GLOBAL_SCAN_CACHE:
            cached_time, cached_data = _GLOBAL_SCAN_CACHE[cache_key]
            if now - cached_time < _SCAN_CACHE_TTL:
                return cached_data

    if req.universe == "custom" and req.custom_symbols:
        symbols = [s.strip().upper() for s in req.custom_symbols.replace("\n", ",").split(",") if s.strip()]
    elif req.universe in UNIVERSES:
        symbols = UNIVERSES[req.universe]["symbols"]
    else:
        raise HTTPException(status_code=400, detail="Invalid universe or symbols list")

    if req.sector and req.sector in SECTOR_MAP:
        sector_syms = set(SECTOR_MAP[req.sector])
        symbols = [s for s in symbols if s in sector_syms]

    if not symbols:
        raise HTTPException(status_code=400, detail="No symbols found for the selected universe/sector")

    # Limit maximum batch scan per run to 200 for lightning responsiveness
    scan_subset = symbols[:200]

    results = run_batch_scan(
        symbols=scan_subset,
        timeframe=req.timeframe,
        rsi_period=req.rsi_period,
        rsi_threshold=req.rsi_threshold,
        swing_window=req.swing_window,
        min_volume=req.min_volume,
        require_hh_hl=req.require_hh_hl,
        require_rsi=req.require_rsi,
        require_ema_compression=req.require_ema_compression,
        require_pinbar_doji=req.require_pinbar_doji,
        max_ema_spread_pct=req.max_ema_spread_pct,
        filter_circuits=req.filter_circuits,
        require_episodic_pivot=req.require_episodic_pivot,
        require_liquidity_sweep=req.require_liquidity_sweep
    )

    with _SCAN_LOCK:
        _GLOBAL_SCAN_CACHE[cache_key] = (time.time(), results)

    return results


@app.get("/api/scan/stream")
async def execute_scan_stream(
    universe: str = "us_mega_caps",
    custom_symbols: Optional[str] = None,
    timeframe: str = "1d",
    rsi_period: int = 21,
    rsi_threshold: float = 50.0,
    swing_window: int = 3,
    min_volume: float = 0.0,
    require_hh_hl: bool = True,
    require_rsi: bool = True,
    require_ema_compression: bool = False,
    require_pinbar_doji: bool = False,
    max_ema_spread_pct: float = 3.5,
    filter_circuits: bool = True,
    require_episodic_pivot: bool = False,
    require_liquidity_sweep: bool = False,
    sector: Optional[str] = None
):
    """
    Server-Sent Events (SSE) streaming endpoint for live scanner progress.
    """
    if universe == "custom" and custom_symbols:
        symbols = [s.strip().upper() for s in custom_symbols.replace("\n", ",").split(",") if s.strip()]
    elif universe in UNIVERSES:
        symbols = UNIVERSES[universe]["symbols"]
    else:
        symbols = UNIVERSES["us_mega_caps"]["symbols"]

    if sector and sector in SECTOR_MAP:
        sector_syms = set(SECTOR_MAP[sector])
        symbols = [s for s in symbols if s in sector_syms]

    scan_subset = symbols[:200]

    async def event_generator():
        gen = stream_scan(
            symbols=scan_subset,
            timeframe=timeframe,
            rsi_period=rsi_period,
            rsi_threshold=rsi_threshold,
            swing_window=swing_window,
            min_volume=min_volume,
            require_hh_hl=require_hh_hl,
            require_rsi=require_rsi,
            require_ema_compression=require_ema_compression,
            require_pinbar_doji=require_pinbar_doji,
            max_ema_spread_pct=max_ema_spread_pct,
            filter_circuits=filter_circuits,
            require_episodic_pivot=require_episodic_pivot,
            require_liquidity_sweep=require_liquidity_sweep
        )
        for item in gen:
            payload = f"data: {json.dumps(item)}\n\n"
            yield payload
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/chart/{symbol}")
async def get_chart_data(
    symbol: str,
    timeframe: str = "1d",
    range_param: str = "6mo",
    rsi_period: int = 21,
    swing_window: int = 3
):
    """
    Returns full candlestick, volume, indicator, swing markers, Market Profile,
    Fair Value Gaps, Liquidity Sweeps, and Trade Psychology metadata.
    """
    symbol = symbol.strip().upper()
    df, meta = get_stock_data(symbol, interval=timeframe, data_range=range_param)

    if df is None or len(df) == 0:
        if symbol == "NVDA":
            fallback = load_default_nvda()
            if fallback:
                return fallback
        raise HTTPException(status_code=404, detail=f"Stock data not found for symbol '{symbol}'. Verify ticker name or try adding .NS for Indian stocks.")

    analysis = analyze_market_structure(
        df,
        rsi_period=rsi_period,
        swing_window=swing_window
    )

    if not analysis.get("is_valid"):
        analysis["passes_scan"] = False
        analysis["trend_status"] = analysis.get("error", "Insufficient data")

    # Candlestick Series: [{ time, open, high, low, close }]
    candles = []
    volumes = []
    rsi_series = []
    ema_10_series = []
    ema_20_series = []
    ema_50_series = []
    ema_200_series = []

    for i in range(len(df)):
        row = df.iloc[i]
        t = int(row["time"])
        o = float(row["open"])
        h = float(row["high"])
        l = float(row["low"])
        c = float(row["close"])
        v = float(row["volume"])

        candles.append({"time": t, "open": o, "high": h, "low": l, "close": c})

        # Volume color matched to candle direction
        vol_color = "rgba(16, 185, 129, 0.45)" if c >= o else "rgba(239, 68, 68, 0.45)"
        volumes.append({"time": t, "value": v, "color": vol_color})

        # RSI series
        if "rsi_21" in df.columns and not row.isna()["rsi_21"]:
            rsi_series.append({"time": t, "value": round(float(row["rsi_21"]), 2)})

        # EMA series
        if "ema_10" in df.columns and not row.isna()["ema_10"]:
            ema_10_series.append({"time": t, "value": round(float(row["ema_10"]), 2)})
        if "ema_20" in df.columns and not row.isna()["ema_20"]:
            ema_20_series.append({"time": t, "value": round(float(row["ema_20"]), 2)})
        if "ema_50" in df.columns and not row.isna()["ema_50"]:
            ema_50_series.append({"time": t, "value": round(float(row["ema_50"]), 2)})
        if "ema_200" in df.columns and not row.isna()["ema_200"]:
            ema_200_series.append({"time": t, "value": round(float(row["ema_200"]), 2)})

    meta_entry = STOCK_METADATA_MAP.get(symbol, {})
    company_name = meta_entry.get("name", symbol)
    sector = meta_entry.get("sector", "Equities")
    industry = meta_entry.get("industry", "Equity")

    return {
        "symbol": symbol,
        "company_name": company_name,
        "sector": sector,
        "industry": industry,
        "meta": meta,
        "analysis": analysis,
        "candles": candles,
        "volumes": volumes,
        "rsi": rsi_series,
        "ema_10": ema_10_series,
        "ema_20": ema_20_series,
        "ema_50": ema_50_series,
        "ema_200": ema_200_series,
        "markers": analysis.get("markers", []),
        "market_profile": analysis.get("market_profile", {}),
        "fair_value_gaps": analysis.get("fair_value_gaps", []),
        "liquidity_sweeps": analysis.get("liquidity_sweeps", []),
        "episodic_pivot": analysis.get("episodic_pivot", {}),
        "trade_psychology": analysis.get("trade_psychology", {}),
        "is_circuit_locked": analysis.get("is_circuit_locked", False),
        "orderflow": {
            "poc": analysis.get("market_profile", {}).get("poc", 0.0),
            "vah": analysis.get("market_profile", {}).get("vah", 0.0),
            "val": analysis.get("market_profile", {}).get("val", 0.0),
            "profile_shape": analysis.get("market_profile", {}).get("profile_shape", "D_SHAPE"),
            "auction_location": analysis.get("market_profile", {}).get("location", "INSIDE_VALUE_AREA")
        }
    }


@app.get("/api/quick-quote/{symbol}")
async def get_quick_quote(symbol: str):
    """Instant single-ticker diagnosis."""
    res = scan_single_stock(symbol)
    return res


@app.post("/api/backtest")
async def run_backtest_endpoint(req: BacktestRequest):
    """
    Executes a comprehensive historical strategy backtest.
    Returns: win rate, profit factor, max drawdown, equity curve, and trade log.
    """
    result = run_strategy_backtest(
        symbol=req.symbol,
        timeframe=req.timeframe,
        data_range=req.data_range,
        strategy=req.strategy,
        risk_reward=req.risk_reward,
        initial_capital=req.initial_capital,
        risk_per_trade_pct=req.risk_per_trade_pct
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message", "Backtest failed"))
    return result


@app.get("/api/backtest/quick/{symbol}")
async def quick_backtest_endpoint(
    symbol: str,
    strategy: str = "master",
    timeframe: str = "1d",
    data_range: str = "1y",
    risk_reward: float = 2.0
):
    """1-Click quick backtest on the currently loaded ticker."""
    result = run_strategy_backtest(
        symbol=symbol,
        timeframe=timeframe,
        data_range=data_range,
        strategy=strategy,
        risk_reward=risk_reward
    )
    return result
    
class AdvancedBacktestRequest(BaseModel):
    symbol: str
    timeframe: str = "1d"
    data_range: str = "2y"
    ast_json: Optional[Dict[str, Any]] = None
    run_monte_carlo: bool = True
    run_walk_forward: bool = False

@app.post("/api/backtest/advanced")
async def advanced_backtest_endpoint(req: AdvancedBacktestRequest):
    """Runs the Phase 4 Event-Driven Backtester with Slippage, Monte Carlo, and WFO."""
    from backtest_engine.engine import EventDrivenBacktester
    from backtest_engine.metrics import calculate_metrics
    from backtest_engine.monte_carlo import MonteCarloEngine
    from backtest_engine.walk_forward import WalkForwardOptimizer
    from data_feed import get_stock_data
    from technicals import analyze_market_structure
    import pandas as pd

    # Fetch Data
    df, meta = get_stock_data(req.symbol, interval=req.timeframe, data_range=req.data_range)
    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="Failed to fetch data.")
        
    analyze_market_structure(df)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], unit="s")

    # Run Event-Driven Loop
    engine = EventDrivenBacktester(symbol=req.symbol, data=df, strategy_ast=req.ast_json)
    equity_curve, trades = engine.run()
    
    # Calculate Institutional Metrics
    metrics = calculate_metrics(equity_curve, trades)
    
    mc_results = {}
    if req.run_monte_carlo and trades:
        # Extract Realized PnLs
        buy_price = 0
        pnl_list = []
        for t in trades:
            if t['direction'] == 'BUY':
                buy_price = t['price']
            elif t['direction'] == 'SELL' and buy_price > 0:
                pnl = (t['price'] - buy_price) * t['quantity']
                pnl -= (t['commission'] * 2) + (t['slippage'] * 2)
                pnl_list.append(pnl)
                buy_price = 0
                
        mc_engine = MonteCarloEngine(pnl_list)
        mc_results = mc_engine.run_simulation(iterations=500)
        
    return {
        "status": "success",
        "symbol": req.symbol,
        "metrics": metrics,
        "monte_carlo": mc_results,
        "equity_curve": equity_curve.reset_index().to_dict(orient="records") if not equity_curve.empty else []
    }


class NlpStrategyRequest(BaseModel):
    query: str

@app.post("/api/strategy/parse")
async def parse_nlp_strategy(req: NlpStrategyRequest):
    """Translates plain English query to Visual Scanner AST JSON."""
    from scanner_engine.nlp_parser import NLPParser
    ast = NLPParser.parse_query(req.query)
    return {"query": req.query, "ast": ast}


class HistoricalExportRequest(BaseModel):
    universe: str
    custom_symbols: Optional[str] = None
    ast_json: Dict[str, Any]
    years: int = 1
    format: str = "parquet"
    strategy_name: str = "custom_strategy"

@app.post("/api/export/scan")
async def export_historical_scan(req: HistoricalExportRequest):
    """Runs a visual scanner strategy over 1-10 years and exports results."""
    from scanner_engine.historical_export import HistoricalScannerEngine
    from stock_lists import UNIVERSES

    if req.universe == "custom" and req.custom_symbols:
        symbols = [s.strip().upper() for s in req.custom_symbols.replace("\n", ",").split(",") if s.strip()]
    elif req.universe in UNIVERSES:
        symbols = UNIVERSES[req.universe]["symbols"]
    else:
        raise HTTPException(status_code=400, detail="Invalid universe.")

    # Restrict symbol count in Demo to prevent massive memory usage
    symbols = symbols[:30]

    engine = HistoricalScannerEngine(export_dir="exports")
    df = engine.run_historical_scan(
        symbols=symbols,
        ast_json=req.ast_json,
        years=req.years
    )
    
    if df.empty:
        return {"status": "success", "message": "No historical signals met the criteria.", "download_url": None, "count": 0}

    filepath = engine.export_results(df, strategy_name=req.strategy_name, format_type=req.format)
    # Expose generic path for downloading
    download_url = f"/api/download?file={filepath.replace('exports/', '')}"
    return {
        "status": "success",
        "message": f"Successfully exported {len(df)} historical signals.",
        "download_url": download_url,
        "count": len(df)
    }

from fastapi.responses import FileResponse
import os

@app.get("/api/download")
async def download_export(file: str):
    """Allows downloading the Parquet/CSV generated exports."""
    # Security: Ensure it stays inside exports directory
    clean_file = os.path.basename(file)
    path = os.path.join("exports", clean_file)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=clean_file)


class PsychologyRequest(BaseModel):
    trades: List[Dict[str, Any]]
    order_modifications: Optional[List[Dict[str, Any]]] = []

@app.get("/api/learning/modules")
async def get_education_modules():
    """Returns all Auction Theory education modules."""
    from learning_engine.education import get_all_modules
    return {"status": "success", "modules": get_all_modules()}

@app.post("/api/psychology/analyze")
async def analyze_psychology(req: PsychologyRequest):
    """Analyzes a batch of trades for behavioral anti-patterns."""
    from learning_engine.psychology import PsychologyCockpit
    from datetime import datetime
    
    # Pre-process timestamps since JSON sends them as strings
    trades_clean = []
    for t in req.trades:
        # Avoid mutating the original dict in a weird way, create a copy
        t_copy = dict(t)
        if isinstance(t_copy.get('timestamp'), str):
            t_copy['timestamp'] = datetime.fromisoformat(t_copy['timestamp'].replace('Z', '+00:00'))
        trades_clean.append(t_copy)
        
    mods_clean = []
    for m in req.order_modifications:
        m_copy = dict(m)
        if isinstance(m_copy.get('timestamp'), str):
            m_copy['timestamp'] = datetime.fromisoformat(m_copy['timestamp'].replace('Z', '+00:00'))
        mods_clean.append(m_copy)

    cockpit = PsychologyCockpit()
    result = cockpit.analyze_session(trades_clean, mods_clean)
    
    return {"status": "success", "analysis": result}


@app.get("/api/heatmap/sectors")
async def get_sector_heatmap():
    """Returns the D3 Treemap JSON for Market Sectors & Industries."""
    from heatmap_engine.sectors import SectorHeatmapEngine
    from heatmap_engine.data_map import SECTOR_MAP
    symbols = list(SECTOR_MAP.keys())
    engine = SectorHeatmapEngine(symbols)
    tree = engine.generate_heatmap()
    return {"status": "success", "heatmap": tree}

@app.get("/api/heatmap/breadth")
async def get_market_breadth():
    """Returns Advance/Decline and EMA Breadth."""
    from heatmap_engine.breadth import MarketBreadthEngine
    from heatmap_engine.data_map import SECTOR_MAP
    symbols = list(SECTOR_MAP.keys())
    engine = MarketBreadthEngine(symbols)
    breadth = engine.calculate_breadth()
    return {"status": "success", "breadth": breadth}

@app.get("/api/heatmap/rotation")
async def get_institutional_rotation():
    """Returns Capital Flows between Risk-On and Risk-Off sectors."""
    from heatmap_engine.rotation import InstitutionalRotationTracker
    from heatmap_engine.data_map import SECTOR_MAP
    symbols = list(SECTOR_MAP.keys())
    tracker = InstitutionalRotationTracker(symbols)
    rotation = tracker.calculate_flows()
    return {"status": "success", "rotation": rotation}


from admin.telemetry import TelemetryMiddleware
app.add_middleware(TelemetryMiddleware)

@app.get("/api/auth/me")
async def get_current_user_profile(user = Depends(get_current_user)):
    """Returns the authenticated user's profile and their billing limits."""
    from auth.billing import get_user_limits
    limits = get_user_limits(user)
    return {
        "status": "success",
        "user": {
            "id": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "organization": user.organization
        },
        "billing_limits": limits
    }

@app.get("/api/admin/telemetry")
async def get_system_telemetry(user = Depends(require_roles([Role.ADMIN]))):
    """Admin-only endpoint to view live system metrics."""
    from admin.telemetry import get_telemetry_metrics
    metrics = get_telemetry_metrics()
    return {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat(),
        "requested_by": user.email,
        "metrics": metrics
    }


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus exposition format for scraping."""
    from admin.telemetry import get_telemetry_metrics
    from fastapi.responses import PlainTextResponse
    
    metrics = get_telemetry_metrics()
    
    lines = [
        "# HELP alphapulse_http_requests_total The total number of HTTP requests.",
        "# TYPE alphapulse_http_requests_total counter",
        f"alphapulse_http_requests_total {metrics['total_requests']}",
        
        "# HELP alphapulse_http_errors_total The total number of HTTP errors.",
        "# TYPE alphapulse_http_errors_total counter",
        f"alphapulse_http_errors_total {metrics['errors']}",
        
        "# HELP alphapulse_avg_response_time_ms Average response time in ms.",
        "# TYPE alphapulse_avg_response_time_ms gauge",
        f"alphapulse_avg_response_time_ms {metrics['avg_response_time_ms']}",
    ]
    
    # Per endpoint metrics
    lines.append("# HELP alphapulse_endpoint_hits_total Endpoint hit counts.")
    lines.append("# TYPE alphapulse_endpoint_hits_total counter")
    for path, data in metrics['endpoints'].items():
        lines.append(f'alphapulse_endpoint_hits_total{{path="{path}"}} {data["hits"]}')
        
    return PlainTextResponse("\n".join(lines) + "\n")


if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading
    import socket

    def find_free_port(start_port=8000):
        for p in range(start_port, start_port + 20):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", p))
                    return p
                except OSError:
                    continue
        return start_port

    port = find_free_port(8000)

    def open_browser():
        import time
        time.sleep(1.2)
        webbrowser.open(f"http://127.0.0.1:{port}")

    threading.Thread(target=open_browser, daemon=True).start()
    print(f"\n==========================================================")
    print(f"  [+] AlphaPulse Stock Scanner & Trading Terminal is LIVE!")
    print(f"  Access URL: http://127.0.0.1:{port}")
    print(f"==========================================================\n")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
