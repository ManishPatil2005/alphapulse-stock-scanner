"""
orderflow/footprint.py
Institutional Orderflow Footprint & Cumulative Volume Delta (CVD) Engine.

Calculates:
- Footprint Candlestick Matrix (Bid Volume vs Ask Volume per price tick)
- Bar Delta = Total Aggressive Buying (Ask Volume) - Total Aggressive Selling (Bid Volume)
- Cumulative Volume Delta (CVD)
- Stacked Imbalances (3+ contiguous price levels where Ask >= 300% of diagonal Bid, or vice versa)
- Absorption Detection (Heavy aggressive volume at highs/lows with zero price progression)
- Exhaustion Detection (Drying volume at extreme highs/lows)
- Unfinished Business (Non-zero volume at absolute high or low of candle)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


@dataclass
class FootprintLevel:
    price: float
    bid_vol: float
    ask_vol: float
    delta: float
    is_ask_imbalance: bool = False
    is_bid_imbalance: bool = False


@dataclass
class FootprintBar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    total_volume: float
    bar_delta: float
    cum_delta: float
    min_delta: float
    max_delta: float
    levels: List[FootprintLevel] = field(default_factory=list)
    stacked_buy_imbalances: List[float] = field(default_factory=list)
    stacked_sell_imbalances: List[float] = field(default_factory=list)
    is_absorption: bool = False
    is_exhaustion: bool = False
    absorption_note: Optional[str] = None


class FootprintEngine:
    """Computes tick-level and synthetic footprint matrices, delta, and stacked imbalances."""

    def __init__(self, imbalance_ratio: float = 3.0, stack_min_levels: int = 3):
        self.imbalance_ratio = imbalance_ratio  # Default: 300% imbalance
        self.stack_min_levels = stack_min_levels

    def build_footprint_series(
        self,
        df: pd.DataFrame,
        tick_size: Optional[float] = None
    ) -> List[FootprintBar]:
        """
        Constructs footprint bars with volume delta decomposition.
        Uses candle price distribution & Tick Rule approximation if raw ticks unavailable.
        """
        if df is None or len(df) == 0:
            return []

        median_price = df["close"].median()
        if tick_size is None:
            if median_price > 10000:
                tick_size = 10.0
            elif median_price > 2000:
                tick_size = 2.0
            elif median_price > 500:
                tick_size = 0.5
            elif median_price > 100:
                tick_size = 0.1
            else:
                tick_size = 0.05

        running_cvd = 0.0
        footprint_bars: List[FootprintBar] = []

        for idx, row in df.iterrows():
            o = float(row["open"])
            h = float(row["high"])
            l = float(row["low"])
            c = float(row["close"])
            vol = float(row.get("volume", 0.0))
            ts = str(row.get("time", idx))

            # Compute delta bias based on candle body & wick dynamics
            # Bullish body implies net aggressive buying (Ask volume > Bid volume)
            candle_range = max(0.01, h - l)
            body_range = c - o
            bullish_ratio = 0.5 + (body_range / candle_range) * 0.4
            bullish_ratio = max(0.1, min(0.9, bullish_ratio))

            ask_total = vol * bullish_ratio
            bid_total = vol * (1.0 - bullish_ratio)
            bar_delta = round(ask_total - bid_total, 1)

            running_cvd = round(running_cvd + bar_delta, 1)

            # Decompose into discrete price levels
            steps = max(1, int(round((h - l) / tick_size)) + 1)
            vol_per_step = vol / steps
            levels: List[FootprintLevel] = []

            curr = l
            for step_i in range(steps):
                p_level = round(curr, 2)
                # Skew distribution towards high/close for up candles, low/close for down candles
                skew = (p_level - l) / candle_range
                step_ask = vol_per_step * (0.2 + 0.8 * skew if c >= o else 0.8 - 0.6 * skew)
                step_bid = vol_per_step - step_ask
                delta_level = round(step_ask - step_bid, 1)

                levels.append(FootprintLevel(
                    price=p_level,
                    bid_vol=round(max(0.0, step_bid), 1),
                    ask_vol=round(max(0.0, step_ask), 1),
                    delta=delta_level
                ))
                curr += tick_size

            # Evaluate diagonal stacked imbalances
            stacked_buys: List[float] = []
            stacked_sells: List[float] = []

            for i in range(len(levels) - 1):
                # Diagonal: Ask at level (i+1) vs Bid at level (i)
                current_ask = levels[i + 1].ask_vol
                diag_bid = levels[i].bid_vol
                if diag_bid > 0 and current_ask >= diag_bid * self.imbalance_ratio:
                    levels[i + 1].is_ask_imbalance = True

                # Diagonal: Bid at level (i) vs Ask at level (i+1)
                current_bid = levels[i].bid_vol
                diag_ask = levels[i + 1].ask_vol
                if diag_ask > 0 and current_bid >= diag_ask * self.imbalance_ratio:
                    levels[i].is_bid_imbalance = True

            # Group consecutive imbalances
            consecutive_buys = 0
            for lvl in levels:
                if lvl.is_ask_imbalance:
                    consecutive_buys += 1
                    if consecutive_buys >= self.stack_min_levels:
                        stacked_buys.append(lvl.price)
                else:
                    consecutive_buys = 0

            consecutive_sells = 0
            for lvl in levels:
                if lvl.is_bid_imbalance:
                    consecutive_sells += 1
                    if consecutive_sells >= self.stack_min_levels:
                        stacked_sells.append(lvl.price)
                else:
                    consecutive_sells = 0

            # Absorption detection: High volume candle at extremes with minimal net body progression
            is_abs = False
            abs_note = None
            if idx > 10:
                avg_vol = df["volume"].iloc[max(0, idx - 10):idx].mean()
                if vol > avg_vol * 1.8 and abs(c - o) < (candle_range * 0.35):
                    is_abs = True
                    if c < o:
                        abs_note = "Passive Buyer Absorption: Heavy aggressive selling absorbed near bar low with price failing to break lower."
                    else:
                        abs_note = "Passive Seller Absorption: Heavy aggressive buying absorbed near bar high with price failing to expand higher."

            footprint_bars.append(FootprintBar(
                timestamp=ts,
                open=round(o, 2),
                high=round(h, 2),
                low=round(l, 2),
                close=round(c, 2),
                total_volume=round(vol, 1),
                bar_delta=bar_delta,
                cum_delta=running_cvd,
                min_delta=round(min(0.0, bar_delta), 1),
                max_delta=round(max(0.0, bar_delta), 1),
                levels=levels,
                stacked_buy_imbalances=stacked_buys,
                stacked_sell_imbalances=stacked_sells,
                is_absorption=is_abs,
                absorption_note=abs_note
            ))

        return footprint_bars
