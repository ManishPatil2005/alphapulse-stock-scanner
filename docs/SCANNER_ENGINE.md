# Scanner Engine Specification

## 1. Visual No-Code Scanner Builder
Provides a drag-and-drop graphical interface to build complex scanning strategies without coding.
- **Logical Connectors:** Supports AND, OR, NOT, and nested groups.
- **Condition Types:** Comparison (`>`, `<`, `=`, `crosses above`, `crosses below`), Range (`between X and Y`), Rank (`top N%`, `bottom N%`).
- **Condition Categories:**
  - **Technical:** RSI, MACD, EMA crossovers, ATR, Bollinger Bands, VWAP.
  - **Structure:** HH/HL, LL/LH, consolidation width, breakout detection.
  - **Volume:** Volume spike (>2x avg), volume dry-up (<0.5x avg), OBV trend.
  - **Orderflow:** Delta positive/negative, absorption detected, imbalance stacking, FVG present.
  - **Market Profile:** Price above/below POC, inside/outside value area, IB range expansion.
  - **Fundamental:** Market cap range, P/E range, sector filter, earnings within N days.
  - **Circuit Filter:** Exclude upper/lower circuit locked stocks.
  - **Episodic Pivot:** Gap up >3% on >2x volume after earnings.
- **UI Specification:** Left panel (condition palette), center (logic canvas), right (preview/results).

## 2. NLP Autonomous Strategy Generator
Translates natural language directly into executable scanners.
- **Flow:** 
  1. Plain English Input: *"stocks breaking 20 day consolidation with volume expansion and strong sector breadth"*
  2. NLP parsing via LLM -> AST (Abstract Syntax Tree) conversion.
  3. AST -> Condition Graph mapping.
  4. Executable Scanner compilation -> Backtest -> Report.
- **Ambiguity Resolution:** LLM integration prompts the user for clarification to resolve vagueness.

## 3. Real-time Streaming Scanner
WebSocket-fed live scanner that re-evaluates conditions dynamically.
- **Evaluation Engine:** 
  - Pre-filters universe to avoid unnecessary compute.
  - Caches intermediate indicator states.
  - Re-evaluates conditions *only* for symbols that receive a tick/candle update.
- **Delivery:** Streams results progressively to the frontend via SSE or WebSockets.

## 4. Historical Scanner Validation
Allows users to backtest their scan criteria against historical data.
- **Capabilities:** Test criteria against 1, 3, 5, 10 years of historical data.
- **User Parameters:** Date range, universe, sector, strategy.
- **Outputs:** Inspect historical scanner outputs with full analysis context. Export to CSV, Parquet, JSON.

## 5. Stock Universe Management
- **Scale:** Supports 5000+ cash segment equities with sector and industry metadata.
- **Pre-defined Universes:** 
  - NSE: Nifty 50, Nifty 100, Nifty 200, Nifty 500, All NSE Cash.
  - US: S&P 500, Nasdaq 100, Russell 2000.
  - Crypto: Top 100 by Market Cap.
- **Custom Watchlists:** Support for user-defined lists.
- **Circuit Filters:** Automatically exclude UC/LC stocks.

## 6. Scan Templates
- Save, load, version, and share scan configurations.
- **Marketplace:** A community hub to share and rate template configurations.
- **Version History:** Includes diff view to track changes over time.

## 7. Performance
- **Speed:** Capable of scanning 5000 stocks in **< 30 seconds**.
- **Tech Stack:** Utilizes parallel evaluation mechanisms (e.g., vectorized matching using DuckDB/Polars).
