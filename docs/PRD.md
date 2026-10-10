# Product Requirements Document (PRD)

## 1. Executive Summary & Platform Vision
The platform is an institutional-grade market intelligence, orderflow analysis, scanning, strategy creation, backtesting, and learning platform. 
**Vision:** Teach traders how markets operate and allow them to create, test, and validate ideas using data.
**Core Philosophy:** The platform **never** outputs BUY, SELL, or HOLD signals. Instead, it provides Market Context, Auction Context, Structure Context, Liquidity Context, and Orderflow Observations, teaching users the "why" behind market movements based on Auction Market Theory and microstructure dynamics.

## 2. User Personas
- **Retail Swing Trader:** Seeks daily/weekly structural shifts, macro volume profiles, and trend analysis.
- **Day Trader:** Relies on intraday orderflow, footprints, cumulative volume delta (CVD), and liquidity sweeps.
- **Prop Desk Trader:** Requires robust backtesting, heatmaps, cross-asset correlations, and sub-millisecond data processing.
- **Quant Researcher:** Focuses on massive historical datasets, regime analysis, API access, and algorithmic strategy validation.
- **Institutional Portfolio Manager:** Needs macro-level asset allocation tools, risk modeling, and execution algorithms.
- **Market Making Desk:** Needs deep orderbook visibility, latency analysis, and liquidity distribution heatmaps.

## 3. Core Modules
- **Stock Scanner:** Real-time and historical condition-based filtering.
- **Orderflow Terminal:** Footprint charts, CVD, imbalances, absorption, and exhaustion.
- **Market Profile:** Time-Price Opportunity (TPO) charts, value areas, single prints.
- **Volume Profile:** Volume nodes, Point of Control (POC), value areas.
- **Heatmaps:** Orderbook depth and liquidity heatmaps.
- **Strategy Builder:** No-code visual builder and NLP-based autonomous strategy generator.
- **Backtesting Engine:** Monte Carlo, walk-forward, regime-specific testing, and options strategies.
- **Learning Platform:** Interactive modules on auction theory, market microstructure, and psychology.
- **Institutional Dashboard:** Multi-tenancy, RBAC, API usage, and advanced reporting.

## 4. Asset Classes
- **Equity:** Global stocks.
- **Index:** Major global indices.
- **Futures:** Index, commodity, currency, and bond futures.
- **Options:** Equity and index options (including Greeks).
- **Crypto:** Spot and derivatives.
- **Forex:** Major and minor pairs.
- **Commodity:** Hard and soft commodities.

## 5. Functional Requirements (Select Modules)
### Orderflow Terminal
- **FR.OF.1:** Render tick-level footprint charts with bid/ask volume splits.
- **FR.OF.2:** Highlight volume imbalances (e.g., 300% delta).
- **Acceptance Criteria:** Footprint renders within 50ms of tick arrival; imbalances visually pop based on customizable thresholds.

### Strategy Builder
- **FR.SB.1:** NLP interface to translate text into logical conditions (e.g., "Find stocks with POC migration higher and positive CVD").
- **FR.SB.2:** Visual block builder for linking conditions.
- **Acceptance Criteria:** NLP parses 95% of predefined syntax accurately; outputs valid Python/Rust query structure.

## 6. Non-Functional Requirements
- **Latency:** <50ms for UI tick rendering; <10ms for WebSocket processing.
- **Throughput:** Capable of handling 10,000+ ticks/sec per user session.
- **Availability:** 99.9% uptime SLA.
- **Data Retention:** 10+ years of historical tick and 1-minute data for backtesting.
- **Scalability:** Kubernetes-native auto-scaling based on CPU/memory and WebSocket connection counts.

## 7. Output Philosophy
The platform acts as an educational and analytical engine. Outputs are structured as:
- **Market Context:** e.g., "Market is balancing within yesterday's value area."
- **Auction Context:** e.g., "Responsive buying seen at the lower value area."
- **Structure Context:** e.g., "Poor high indicates unfinished auction."
- **Liquidity Context:** e.g., "Thick liquidity resting 5 ticks below current price."
- **Orderflow Observations:** e.g., "Aggressive selling absorbed by passive bids at $150."
- **Scenario Analysis:** e.g., "If price breaches $150, next liquidity node is at $148."
- **Teaching Notes:** e.g., "Notice how the POC migrated lower while price increased—a classic divergence."
- **CRITICAL:** NEVER output BUY/SELL/HOLD.

## 8. User Stories
- *As a Day Trader, I want to see cumulative volume delta (CVD) divergences so I can identify potential exhaustion points.*
- *As a Quant Researcher, I want to export 5 years of option chain data via API so I can train a machine learning model.*
- *As a Retail Swing Trader, I want to learn about Market Profile through interactive platform annotations so I can understand institutional positioning.*

## 9. Priority Matrix
| Feature | Priority | Phase |
|---------|----------|-------|
| Data Provider Abstraction | P0 | 1 |
| Basic Charting & Normalization | P0 | 1 |
| Volume/Market Profile | P1 | 2 |
| Orderflow (Footprints, CVD) | P1 | 3 |
| Backtesting Engine | P1 | 5 |
| NLP Strategy Builder | P2 | 4 |
| Learning Platform | P2 | 6 |
| Institutional Dashboard | P3 | 7 |
