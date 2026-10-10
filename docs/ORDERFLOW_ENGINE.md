# Orderflow & Market Microstructure Engine Specification

## 1. Theoretical Foundation
The engine is built on **Auction Market Theory** (James Dalton) and **Market Generated Information**. Its core philosophy is to extract context from liquidity and volume rather than price alone. 

**IMPORTANT NOTE:** The platform serves as an educational and analytical tool. It outputs context, observations, and structural mapping. **It NEVER generates automated BUY/SELL/HOLD signals.**

## 2. Market Profile (TPO) Engine
- **TPO Construction:** Calculates Time Price Opportunities over 30-minute brackets (A-period, B-period, etc.).
- **Initial Balance (IB):** The price range established during the first 30/60 minutes of trading.
- **Value Area:** Identifies the price range where 70% of the TPO volume occurred.
  - **POC (Point of Control):** Price level with the highest TPO count.
  - **VAH / VAL:** Value Area High and Value Area Low.
- **Profile Shapes:** Classifies daily structures into Normal, p-shaped (short covering), b-shaped (long liquidation), D-shaped, and Double Distribution.
- **Multi-day Composites:** Merges adjacent profiles to map macro balance areas.
- **TPO Count:** Maintained per price level per time period.

## 3. Volume Profile Engine
- **Calculation:** Distributes traded volume across specific price levels instead of time.
- **Key Metrics:**
  - VPOC (Volume Point of Control).
  - Volume-weighted value area.
  - High Volume Nodes (HVN) and Low Volume Nodes (LVN).
- **Modes:** Fixed range, Session, Visible Range, and custom range profiles.
- **Delta-Weighted Profile:** Colors volume nodes by aggressive buy vs. aggressive sell volume.

## 4. Footprint Chart Engine
- **Trade Classification:** Uses the Tick Rule (uptick = buy, downtick = sell) or exchange-provided trade side to classify volume.
- **Matrix Construction:** Builds a per-candle bid/ask volume matrix.
- **Delta per price level:** (ask volume - bid volume).
- **Imbalance Detection:** 
  - Diagonal imbalance detection.
  - **Stacked Imbalances:** Detects 3+ consecutive imbalance ratios >300%.
- **Auction Extremes:** Detects finished vs. unfinished auctions.

## 5. CVD (Cumulative Volume Delta) Engine
- **Delta Calculation:** Running delta calculation across sessions.
- **Divergence Detection:** 
  - E.g., Price makes a Higher High, but CVD makes a Lower High (Bearish Divergence).
- **Trend Analysis:** Tracks CVD trend for session-long aggression.

## 6. Absorption & Exhaustion Detection
```python
# Pseudocode for Absorption Detection
def detect_absorption(price_level, tick_data, threshold_volume):
    passive_volume = 0
    aggressive_volume = 0
    for tick in tick_data:
        if tick.price == price_level:
            aggressive_volume += tick.volume
            if price_level_unchanged(tick.timestamp):
                passive_volume += tick.volume
    return passive_volume > threshold_volume

# Pseudocode for Exhaustion Detection
def detect_exhaustion(candle_extremes, delta_history):
    return (candle_extremes.is_high_volume and 
            delta_history.is_diminishing_at_extreme and 
            candle_extremes.shows_reversal)
```
- **Absorption:** Large passive orders absorbing aggressive flow (high volume, no price movement).
- **Exhaustion:** Diminishing delta at price extremes (climactic volume with reversal).

## 7. Smart Money Concepts (SMC) & ICT Module
- **Liquidity Sweeps:** Price pierces a swing high/low then reverses.
- **Fair Value Gap (FVG):** A 3-candle pattern representing an imbalance (bullish: candle 1 high < candle 3 low; bearish: candle 1 low > candle 3 high).
- **Order Blocks:** The last opposing candle before an impulsive move.
- **Breaker Blocks:** Failed order blocks.
- **Mitigation Blocks:** Partially filled FVGs.
- **Market Structure:** Automated mapping of Break of Structure (BOS) and Change of Character (CHoCH).

## 8. Imbalance Detection
- Volume imbalance between bid/ask at each price level.
- Threshold-based detection (configurable, default 300%).
- Stacking rules for institutional conviction.

## 9. Institutional Flow Indicators
- **Big Bar Analysis:** Volume > 2x 20-period average AND range > 1.5x ATR.
- **Operator Trap:** Failed breakouts with volume divergence.
- **Iceberg Detection Framework:** Repeated fills at same price despite expected exhaustion.

## 10. Output Format
All observations serve strictly as educational context, mapping out the institutional narrative. No direct signals.
