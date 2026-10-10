# Project Memory and State Tracking

## Current State
**Phase 0 - Foundation Specifications**
Currently establishing the core architectural specifications and documentation before beginning the major refactoring effort.

## Data Provider Migration
- **Legacy:** Moving away from `yfinance`.
- **Target:** Transitioning to institutional-grade feeds.
  - **Angel One SmartAPI:** For Indian Markets (Equity, F&O).
  - **Delta Exchange:** For Crypto and Crypto Derivatives.

## Credentials Status
- **Angel One:** `CONFIGURED` (API key, client ID, password, TOTP secret are available).
- **Delta Exchange:** `CONFIGURED` (API key, secret are available).

## Technical Debt Tracker
- **Architecture Monolith:** The current codebase relies on a monolithic `app.py` and a single `index.html` template.
- **Action Required:** Immediate need for decomposition into microservices (FastAPI backend, Next.js frontend).
- **Vercel Limitations:** Vercel serverless functions have a 10-second timeout, which breaks SSE (Server-Sent Events) scanning.
- **Caching Issues:** Browser cache is causing stale script issues on the frontend.
- **Data Safety:** Defensive null checks are urgently needed for meta fields processing incoming ticks.

## Key Learnings
- **Infrastructure:** Serverless functions (Vercel) are incompatible with long-lived streaming connections (SSE/WebSockets). A dedicated deployment model (e.g., Docker/K8s/VPS) is required for the real-time engine.
- **UI State:** Strict cache-busting mechanisms are required for active frontend development.

## Architecture Decisions (ADRs)
*Detailed in `DECISIONS.md` (to be created/maintained).*
- **ADR-001:** Adopt Event-Driven Architecture for the backtester.
- **ADR-002:** Migrate from YFinance to Angel One / Delta Exchange for tick-level fidelity.

## Environment & Git
- **Branch:** `main`
- **Deployment:** Vercel at `alphapulse-stock-scanner.vercel.app` (Frontend/Legacy endpoints).

## Critical Issues to Fix (High Priority)
1. **Chart Auto-Scaling:** Prices are rendering at incorrect vertical levels (Lightweight Charts configuration issue).
2. **Live Feed Stability:** Unhandled disconnects in the websocket/data streams.
3. **Instrument Verification:** Need a proper symbol mapping and verification layer before accepting client subscription requests.

## Next Milestone
**Phase 1 - Data Provider Abstraction Layer**
Implement the unified interface to abstract Angel One and Delta Exchange feeds into standardized internal `MarketEvent` streams.
