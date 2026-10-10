# Learning Engine Specification

## 1. Philosophy and Goal
**Mission:** Teach traders how markets operate using Market Generated Information (MGI). 
**Core Rule:** NEVER provide explicit trading advice, signals (BUY/SELL/HOLD), or definitive future predictions. The platform facilitates idea creation, validation, and learning based on data.

## 2. Theoretical Foundations
The educational framework is heavily rooted in institutional trading concepts:
- **Auction Market Theory (AMT):** Inspired by James Dalton. Views the market as a continuous two-way auction seeking fair value.
- **Market Profile:** Value Area (VA), Balance vs. Imbalance, Range Extension, Poor Highs/Lows, Single Prints.
- **Volume Profile:** VPOC migration, Naked POC, Developing vs. Developed profiles, High/Low Volume Nodes (HVN/LVN).
- **Orderflow:** Delta, Absorption, Exhaustion, Initiative vs. Responsive activity.
- **Smart Money Concepts (SMC):** Institutional order flow, liquidity engineering (buy/sell stops), Market Structure Shifts (MSS), Fair Value Gaps (FVG).

## 3. Learning Modules Architecture

| Module | Topic | Key Concepts |
|---|---|---|
| Module 1 | Price as an Advertising Mechanism | Auctions, Price Discovery, Bids vs. Offers |
| Module 2 | TPO & Market Profile Basics | TPO, Initial Balance, Day Types (Normal, Trend, etc.) |
| Module 3 | Value Area & Auction Rotation | VAH, VAL, 80% Rule, Balance transitions |
| Module 4 | Volume Profile & Acceptance | Volume POC, Acceptance vs. Rejection, HVN/LVN |
| Module 5 | Reading Orderflow | Footprint Charts, Bid/Ask Delta, Imbalances |
| Module 6 | Institutional Participation | Iceberg Orders, Spoofing, Absorption |
| Module 7 | Smart Money Concepts (SMC) | Liquidity Pools, FVGs, Order Blocks (OB) |
| Module 8 | Market Regimes | Volatility Analysis, Contextual Overlays |
| Module 9 | Risk & Position Sizing | Math of Drawdowns, Expectancy, Kelly Criterion |
| Module 10| Hypothesis Validation | Building a scientific trading process via backtesting |

## 4. Interactive Teaching Mode

### 4.1 On-Chart Annotations
Dynamically generated text directly on charts based on real-time data events.
*Example output:* "Price has been accepted above yesterday's VAH for 2 periods. According to AMT, this acceptance could indicate the market is auctioning higher to find new responsive sellers."

### 4.2 Tooltips and Replays
- **Contextual Tooltips:** Hovering over an FVG or TPO single print explains the institutional mechanics behind its formation.
- **Historical Replay:** Guided case studies stepping bar-by-bar through historical days with high educational value (e.g., trend days, major news events).

## 5. In-Trade Psychology Cockpit
An integrated dashboard designed to mitigate emotional and cognitive errors during live or simulated execution.

### Features:
1. **FOMO Risk Assessment:** Measures the distance from the user's intended entry to the current momentum extreme (e.g., VWAP deviation).
2. **Revenge Trading Detection:** Flags rapid successive trade entries following a closed loss.
3. **Position Sizing Calculator:** Recommends sizes based on Fixed Fractional or Kelly Criterion models based on user's historical expectancy.
4. **Risk-Reward Visualization:** Visual R-multiple plotting on the DOM and chart.
5. **Emotional State Tracker:** User self-reporting matrix correlated post-trade with P&L.
6. **Cognitive Bias Alerts:** Detects anchoring, recency bias, and confirmation bias based on user interaction patterns.

## 6. Teaching Output Format Guidelines
- **Always Frame as Theory:** "According to Auction Market Theory..." or "Market Profile analysis suggests..."
- **Never Dictate Action:** "Buy here," "Sell now," or "This is a guaranteed trade."
- **Context Layers Required:** Observations must be categorized into:
  - *Market Context* (Macro, Regime)
  - *Auction Context* (Value Areas, TPO)
  - *Structure Context* (Trends, Swings)
  - *Liquidity Context* (Orderflow, Pools)
  - *Scenario Analysis* (If X happens, Y is the theoretical expectation)
