# ⚡ AlphaPulse - Stock Scanner & Trading Terminal (Enterprise Edition)

A high-performance, enterprise-grade Python **Stock Scanner and Trading Terminal** designed to scan entire stock universes and indices (US Markets & Indian NSE/BSE) and identify high-probability uptrending assets satisfying strict Dow Theory structure and momentum criteria:

1. **Price is making Higher Highs (HH) and Higher Lows (HL)**: Market structure confirmation where buyers establish consecutively higher swing peaks and higher swing troughs.
2. **RSI(21) is above 50**: Relative Strength Index calculated over 21 periods confirming bullish momentum control.
3. **Market Structure Integrity**: Current price sustains above the latest swing low support.

---

## 🚀 Key Upgrades & Capabilities

### 1. Instant Search & Autocomplete (`/api/search`)
- Search by **Symbol** OR **Company Name** (e.g. typing `nifty`, `rel`, `tata`, `tsla`, `apple`).
- High-speed in-memory registry indexing US stocks, Indian NSE/BSE companies, and world market indices.
- Keyboard navigation (Arrow Up/Down + Enter) and clickable dropdown.

### 2. Full World & Indian Index Support
- `^NSEI`: NIFTY 50 Index (India)
- `^NSEBANK`: NIFTY Bank Index (India)
- `^BSESN`: BSE SENSEX 30 (India)
- `^CNXIT`: NIFTY IT Index (India)
- `^GSPC`: S&P 500 Index (US)
- `^IXIC`: NASDAQ Composite (US)
- `^DJI`: Dow Jones Industrial Average (US)
- `BTC-USD` & `ETH-USD`: Crypto Market Leaders

### 3. Scalable Architecture for Lakhs (100,000+) of Users
- **Single-Flight Request Deduplication**: Protects against the "Thundering Herd" problem. When 1,000 users request the same chart simultaneously, only 1 upstream request executes; all users receive the identical cached result.
- **Shared In-Memory Scan & Data Cache**: Serves cached charts in **< 15 milliseconds** directly from RAM, completely eliminating Yahoo Finance rate limits (HTTP 429).
- **GZip HTTP Compression**: Enabled via Starlette middleware, compressing candlestick JSON payloads by ~80% to save bandwidth at scale.

### 4. Robust Offline & Local TradingView Lightweight Charts (v4.2)
- Bundled locally inside `static/js/lightweight-charts.standalone.production.js` (no external CDN failure risk).
- Responsive `ResizeObserver` engine that dynamically recalculates canvas dimensions so charts never render collapsed or blank.
- Formatted date strings (`YYYY-MM-DD`) and monotonic time ordering to prevent any assertion glitches.

### 5. Live Auto-Update / Polling
- Live toggle in the header: automatically refreshes the active stock every 5 seconds without screen flicker.
- Pulsing live update badge displaying the exact timestamp of the latest tick.

---

## 🛠 Project Architecture

```
d:\CLIENT 2\
├── app.py                # FastAPI web server, GZip middleware, SSE streaming, and chart API
├── data_feed.py          # Thread-safe data provider with Single-Flight coalescing and TTL caching
├── scanner.py            # Multithreaded parallel scanner engine
├── technicals.py         # Vectorized Wilder's RSI(21), Swing High/Low detection, EMAs, ATR
├── ticker_search.py      # Sub-millisecond in-memory autocomplete index across US, NSE, and Indices
├── stock_lists.py        # Curated universes (US Mega-Caps, NASDAQ 100, NIFTY 50, Indices, etc.)
├── test_app.py           # Automated end-to-end verification suite
├── run.bat               # Windows 1-click double-click launcher
├── templates/
│   └── index.html        # Dashboard layout with search suggestions and responsive layout
├── static/
│   ├── css/style.css     # Bloomberg/TradingView-inspired dark terminal styling
│   └── js/
│       ├── app.js        # Lightweight charts integration, search dropdown, live scanner SSE client
│       └── lightweight-charts.standalone.production.js # Local TradingView Charts v4.2
└── README.md
```

---

## 🏃 How to Run the Application

### Option 1: 1-Click Launch (Recommended)
Double-click `run.bat` in `d:\CLIENT 2`.

### Option 2: Terminal Launch
```powershell
python "d:\CLIENT 2\app.py"
```
The browser will automatically open to `http://127.0.0.1:8000`.

### Option 3: Run the Automated Validation Suite
```powershell
python "d:\CLIENT 2\test_app.py"
```
Verifies search suggestions, US stocks, Indian NSE stocks, World Indices, and concurrent in-memory cache speed.
