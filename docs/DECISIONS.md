# Architecture Decision Records (ADRs)

## ADR-001: Why FastAPI over Django/Flask
- **Status:** Accepted
- **Context:** The backend requires high concurrency, real-time WebSocket support, and modern API validation.
- **Decision:** Use FastAPI for backend services.
- **Consequences:** Native async support, automatic OpenAPI docs, and strict typing via Pydantic. Steeper learning curve for async Python compared to Django.
- **Alternatives Considered:** Django (too heavy, synchronous by default), Flask (lacks native async and validation).

## ADR-002: Why TimescaleDB over InfluxDB/QuestDB
- **Status:** Accepted
- **Context:** We need to store billions of ticks and aggregated candles with complex SQL analytical queries.
- **Decision:** Use TimescaleDB (PostgreSQL extension).
- **Consequences:** We leverage existing PostgreSQL ecosystem, tools, and ORMs. Excellent compression via hypertables.
- **Alternatives Considered:** InfluxDB (custom query language, harder relational joins), QuestDB (fast but smaller ecosystem).

## ADR-003: Why DuckDB for analytics
- **Status:** Accepted
- **Context:** Fast analytical queries (OLAP) are required for scanning and backtesting without taxing the primary transactional database.
- **Decision:** Embed DuckDB in the scanning and backtesting microservices.
- **Consequences:** Zero-copy integration with Apache Arrow and Pandas. Extremely fast aggregations on local Parquet files.
- **Alternatives Considered:** ClickHouse (requires separate cluster management).

## ADR-004: Why Kafka over RabbitMQ/Redis Streams for tick fanout
- **Status:** Accepted
- **Context:** Raw ticks need to be reliably distributed to aggregators, scanners, and websocket fanouts in correct order.
- **Decision:** Use Apache Kafka.
- **Consequences:** High throughput, guaranteed ordering per partition (symbol), replayability for missed messages. Increased infrastructure complexity.
- **Alternatives Considered:** RabbitMQ (poor replayability), Redis Streams (memory limits for historical retention).

## ADR-005: Why TradingView Lightweight Charts over D3/Plotly
- **Status:** Accepted
- **Context:** The frontend needs a high-performance chart that understands financial data (time series, OHLC, price scales) natively.
- **Decision:** Use TradingView Lightweight Charts.
- **Consequences:** WebGL performance, out-of-the-box financial interactions, easy overlay API. 
- **Alternatives Considered:** D3.js (too low-level), Plotly (heavy, slow for real-time 60fps updates).

## ADR-006: Why Next.js over plain React/Svelte
- **Status:** Accepted
- **Context:** The web application requires robust routing, SEO capabilities for learning content, and seamless API integration.
- **Decision:** Use Next.js App Router.
- **Consequences:** Server-Side Rendering (SSR) available, easy deployment on Vercel/Docker, strong ecosystem.
- **Alternatives Considered:** Plain React SPA (poor SEO), SvelteKit (smaller community/ecosystem for financial libs).

## ADR-007: Why Angel One SmartAPI as primary Indian feed
- **Status:** Accepted
- **Context:** Institutional grade platform requires deep orderbook data (L2/L3), low latency, and broad F&O coverage for Indian markets.
- **Decision:** Use Angel One SmartAPI.
- **Consequences:** Provides binary WebSocket feeds and rich F&O coverage. Requires careful handling of rate limits.
- **Alternatives Considered:** Zerodha Kite Connect (more expensive, rate limits), Upstox.

## ADR-008: Why Delta Exchange for crypto
- **Status:** Accepted
- **Context:** We need a robust crypto data feed focused on derivatives and orderflow that serves the Indian context well.
- **Decision:** Use Delta Exchange API.
- **Consequences:** High-quality derivative feeds, API reliability.
- **Alternatives Considered:** Binance (regulatory uncertainty in some regions).

## ADR-009: Provider abstraction pattern
- **Status:** Accepted
- **Context:** Data providers change, or users may want to plug in different brokers.
- **Decision:** Implement an Adapter Pattern for all broker integrations.
- **Consequences:** Core system logic is isolated from provider-specific quirks. Swapping a broker requires zero changes to core aggregation engines.
- **Alternatives Considered:** Direct coupling (rejected due to high maintenance burden).

## ADR-010: Why educational output only, never buy/sell signals
- **Status:** Accepted
- **Context:** Generating automated signals poses severe regulatory risks (SEBI/SEC compliance) and reduces pedagogical value.
- **Decision:** The platform will strictly teach concepts (Orderflow, Market Profile) and allow users to validate their own ideas. No default buy/sell signals will be provided.
- **Consequences:** Protects the company from liability. Attracts serious learners rather than "get-rich-quick" users.
- **Alternatives Considered:** Providing signals (rejected due to compliance and ethical considerations).
