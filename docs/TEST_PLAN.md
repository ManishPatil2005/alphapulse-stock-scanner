# Comprehensive Test Plan

## 1. Testing Pyramid Strategy
Our testing architecture follows a strict pyramid distribution to ensure robust CI/CD pipelines without bottlenecking deployments.
- **Unit Testing**: 70% of test suite.
- **Integration Testing**: 20% of test suite.
- **End-to-End (E2E) Testing**: 10% of test suite.

## 2. Unit Testing (pytest & Jest/Vitest)
- **Coverage Target**: Minimum 80% globally. 95% minimum for critical paths (Backtest Engine, Orderflow calculations, Risk logic).
- **Mocks**: Comprehensive mocking of external providers (Angel One SmartAPI, Delta Exchange).
- **Property-Based Testing**: Using the Python `hypothesis` library to fuzz numerical algorithms (e.g., indicator calculations, VWAP math) to ensure robustness across a wide range of price inputs.

## 3. Integration Testing
- **API Endpoints**: Tested via FastAPI `TestClient` to validate routing, middleware, and request/response schemas.
- **Database**: Ephemeral Testcontainers (PostgreSQL, TimescaleDB, Redis) spin up for integration tests to validate complex queries and migrations.
- **WebSocket Lifecycles**: Simulating client connect, subscribe, message stream, and disconnect flows.
- **Feed Provider Replays**: Integration tests run against pre-recorded, deterministic data replays to validate parsers without relying on live market hours.

## 4. End-to-End Testing (Playwright)
Browser automation testing critical user journeys on staging environments:
- Login Flow & Session persistence.
- Searching an instrument and rendering a chart.
- Configuring and running the market scanner.
- Setting up and executing a backtest.
- **Visual Regression Testing**: Pixel-matching chart renders and orderflow heatmaps to detect unintended UI side effects.

## 5. Performance & Load Testing
- **HTTP Load Testing (Locust)**: Target of 1,000 concurrent users with p99 latency < 200ms.
- **Throughput Testing**: Ensuring the Python/FastAPI backend can process >10,000 ticks/second per node without dropping data.
- **WebSocket Fan-Out**: Validating stability with 500 concurrent client subscriptions per pod.
- **Memory Profiling**: Long-running process tests to detect memory leaks, particularly in DataFrame or Arrow operations.

## 6. Chaos Testing
- **Feed Disconnections**: Randomly terminating the Angel One or Delta Exchange WebSocket to verify auto-reconnect and state recovery logic.
- **Database Failover**: Simulating primary DB node crashes to test read-replica promotion and application retry logic.
- **Kafka Failures**: Killing Kafka brokers to ensure backpressure mechanisms function correctly.

## 7. Data Validation Testing
- **Price Normalization**: Ensuring split and dividend adjustments calculate perfectly against known historical datasets.
- **Indicator Accuracy**: Comparing internal EMA, MACD, and Volume Profile calculations against established references (e.g., TA-Lib, TradingView).
- **Backtest Fidelity**: Running deterministic strategies and comparing outputs against manually verified, hand-calculated results.

## 8. Security Testing
- **DAST (Dynamic Application Security Testing)**: Automated OWASP ZAP scans against staging environments.
- **Credential Exposure**: Regex-based scanning of the codebase for accidental hardcoded secrets.
- **Rate Limit Verification**: Purposefully spamming endpoints to ensure 429 Too Many Requests are returned accurately per tier.
- **Auth Boundaries**: Testing horizontal privilege escalation (User A accessing User B's portfolio).
