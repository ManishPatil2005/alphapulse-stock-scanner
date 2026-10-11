# Complete Engineering Overhaul - AlphaPulse

## A. Existing Working Features
- High-Performance AST Scanner Engine
- Institutional Monte Carlo Backtester
- Real-Time Trade Psychology tracking (FOMO Guardrails)
- Heatmap Breadth Engine
- Base Candlestick & Volume Charting
- Angel One & Delta Exchange connectivity logic (Backend)

## B. Missing Features (Now Fixed)
- Indicators (VWAP, BB, MACD, SuperTrend, EMA200) not displayed on frontend.
- Data Feeder auto-scaling error (caused by volume squashing price scales).
- Export CSV Scanner UI button missing.
- Advanced Strategy Backtest execution UI button missing.
- Contextual Market Profile string generation (Jim Dalton / ICT Context).

## C. Stub Implementations
- Native "Orderflow Footprint Grid" (requires WebGL or heavily optimized canvas grid - currently rendering Market Profile POC, VAH, VAL as horizontal PriceLines).

## D. APIs not connected
- None remaining. The backend endpoints `/api/export/scan`, `/api/chart/`, and `/api/scan` are fully bound to the frontend UI.

## E. Frontend components not rendering (Now Fixed)
- `volumeSeries` scaling logic was breaking the entire chart (the "12000 randomly showing as 120" bug). This was fixed by detaching the volume scale margins.
- `institutionalContextText` added to display Market Auction Theory probabilities instead of plain Buy/Sell indicators.

## F. Files Modified
- `templates/index.html` (Major Overhaul)
- `technicals.py` (New custom Indicators without `pandas-ta` dependency, Institutional Context generator)
- `app.py` (API payload expansions)

## G. Exact Fixes Performed
1. **Lightweight Charts Auto-Scale Glitch Fix**: Added explicit `scaleMargins` of `top: 0.85` to the `priceScale('')` of the Volume overlay, preventing volume spikes from compressing price candles.
2. **Zero-Dependency Indicators**: Built completely native pandas/numpy logic for VWAP, Bollinger Bands, and MACD inside `technicals.py` since network restrictions blocked `pandas-ta`.
3. **UI Toggles**: Injected HTML `pill-btn` elements for VWAP, BB, and EMA200, and mapped them to Lightweight Charts boolean visibility states.
4. **Market Profile Visuals**: Mapped the backend's Orderflow VAH, VAL, and POC points to TradingView `PriceLine` injections inside `renderChartData()`.
5. **Dalton / SMC / ICT Probabilities**: Built a string-generator in `technicals.py` that evaluates the FVG, Liquidity Sweeps, and Value Area to output probabilistic context instead of Buy/Sell indicators.
6. **CSV Export / Backtest UI**: Appended dedicated DOM buttons to trigger the historical Parquet/CSV exporter and Strategy backtester endpoints.

## H. Screenshots / Evidence Locations
- **Indicators**: Configured in `templates/index.html` line 2851+ (Click listeners for VWAP, BB, EMA200).
- **Market Profile**: Configured in `templates/index.html` line 2285+ (Red and Blue dashed `createPriceLine` injections).
- **Data Feed Chart Scale Fix**: `templates/index.html` line 2038 (Explicit `applyOptions` for overlay price scale).
- **Context Generation**: Built natively inside `technicals.py` (lines 645-654) and rendered in UI `contextCard`.
