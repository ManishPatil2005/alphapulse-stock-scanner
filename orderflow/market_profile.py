"""
orderflow/market_profile.py
Institutional Market Profile (TPO) Engine based on James Dalton's Auction Market Theory.

Calculates:
- Time Price Opportunities (TPO) distribution
- Initial Balance (IB High, IB Low, IB Range)
- Point of Control (POC / VPOC)
- Value Area High (VAH) & Value Area Low (VAL) covering ~70% of distribution
- Profile Shapes (Normal, 'P' shape, 'b' shape, D-shape / Balance, Double Distribution)
- Single Prints (Liquidity voids / impulse auction areas)
- Auction Context (Initiative vs Responsive activity, Acceptance vs Rejection)

NEVER generates BUY/SELL/HOLD advice. Outputs pure Market Generated Information (MGI).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd


@dataclass
class TPOLevel:
    price: float
    tpo_count: int
    volume: float = 0.0
    periods: List[str] = field(default_factory=list)


@dataclass
class MarketProfileResult:
    symbol: str
    poc: float
    vah: float
    val: float
    ib_high: float
    ib_low: float
    ib_range: float
    range_high: float
    range_low: float
    total_tpos: int
    profile_shape: str
    is_balanced: bool
    single_prints: List[float] = field(default_factory=list)
    auction_context: Dict[str, Any] = field(default_factory=dict)
    tpo_distribution: List[Dict[str, Any]] = field(default_factory=list)


class MarketProfileEngine:
    """Calculates Dalton Time Price Opportunity (TPO) distributions and Auction Market Context."""

    def __init__(self, tick_size: float = 0.5):
        self.tick_size = tick_size

    def calculate_profile(
        self,
        df: pd.DataFrame,
        symbol: str = "TICKER",
        ib_periods: int = 2
    ) -> Optional[MarketProfileResult]:
        """
        Builds the TPO profile from candlestick/intraday dataframe.
        Expected columns: ['time', 'open', 'high', 'low', 'close', 'volume']
        """
        if df is None or len(df) < 5:
            return None

        # Determine dynamic tick bucket size based on price magnitude
        median_price = df["close"].median()
        if median_price > 10000:
            bucket_size = 20.0
        elif median_price > 2000:
            bucket_size = 5.0
        elif median_price > 500:
            bucket_size = 1.0
        elif median_price > 100:
            bucket_size = 0.25
        else:
            bucket_size = 0.05

        price_bins: Dict[float, Dict[str, Any]] = {}
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

        # Calculate Initial Balance (IB: first ib_periods bars)
        ib_df = df.iloc[:min(ib_periods, len(df))]
        ib_high = float(ib_df["high"].max())
        ib_low = float(ib_df["low"].min())
        ib_range = round(ib_high - ib_low, 2)

        total_tpos = 0

        # Construct TPO matrix
        for idx, row in df.iterrows():
            period_letter = letters[idx % len(letters)]
            low_b = math_floor(row["low"], bucket_size)
            high_b = math_ceil(row["high"], bucket_size)

            curr = low_b
            vol_per_step = float(row["volume"]) / max(1, int(round((high_b - low_b) / bucket_size)) + 1)

            while curr <= high_b:
                rounded_p = round(curr, 2)
                if rounded_p not in price_bins:
                    price_bins[rounded_p] = {"count": 0, "volume": 0.0, "periods": []}
                price_bins[rounded_p]["count"] += 1
                price_bins[rounded_p]["volume"] += vol_per_step
                if period_letter not in price_bins[rounded_p]["periods"]:
                    price_bins[rounded_p]["periods"].append(period_letter)
                total_tpos += 1
                curr = round(curr + bucket_size, 4)

        if not price_bins:
            return None

        # Point of Control (POC): Price level with maximum TPO count (or max volume)
        sorted_prices = sorted(price_bins.keys())
        poc = max(sorted_prices, key=lambda p: (price_bins[p]["count"], price_bins[p]["volume"]))

        # Calculate 70% Value Area (VAH & VAL)
        target_tpos = int(total_tpos * 0.70)
        accumulated_tpos = price_bins[poc]["count"]
        val_idx = sorted_prices.index(poc)
        vah_idx = val_idx

        # Expand symmetrically or towards greatest participation
        while accumulated_tpos < target_tpos and (val_idx > 0 or vah_idx < len(sorted_prices) - 1):
            above_count = price_bins[sorted_prices[vah_idx + 1]]["count"] if vah_idx < len(sorted_prices) - 1 else -1
            below_count = price_bins[sorted_prices[val_idx - 1]]["count"] if val_idx > 0 else -1

            if above_count >= below_count and above_count != -1:
                vah_idx += 1
                accumulated_tpos += above_count
            elif below_count != -1:
                val_idx -= 1
                accumulated_tpos += below_count
            else:
                break

        val = sorted_prices[val_idx]
        vah = sorted_prices[vah_idx]
        range_high = sorted_prices[-1]
        range_low = sorted_prices[0]

        # Single Prints (levels with exactly 1 TPO in middle of range, representing swift impulse auction)
        single_prints = [
            p for p in sorted_prices[1:-1]
            if price_bins[p]["count"] == 1 and val < p < vah
        ]

        # Profile Shape Classification
        poc_relative_pos = (poc - range_low) / max(0.01, (range_high - range_low))
        if poc_relative_pos > 0.65:
            profile_shape = "P_SHAPE"       # Short covering / Initiative buying at high
            shape_desc = "P-Shape Profile: Short covering or initiative buyers establishing acceptance at highs."
        elif poc_relative_pos < 0.35:
            profile_shape = "b_SHAPE"       # Long liquidation / Initiative selling at lows
            shape_desc = "b-Shape Profile: Long liquidation or initiative sellers establishing acceptance at lows."
        elif 0.40 <= poc_relative_pos <= 0.60:
            profile_shape = "D_SHAPE"       # Balanced two-sided rotational auction
            shape_desc = "D-Shape Profile: Balanced two-sided rotational auction with clear fair value consensus."
        else:
            profile_shape = "ELONGATED"
            shape_desc = "Elongated Profile: Strong trending one-time-framing market seeking new value."

        current_price = float(df["close"].iloc[-1])
        if current_price > vah:
            location = "ABOVE_VALUE_AREA"
            location_note = "Price auctioning above Value Area High. Testing higher prices for acceptance or rejection."
        elif current_price < val:
            location = "BELOW_VALUE_AREA"
            location_note = "Price auctioning below Value Area Low. Testing lower prices (discount) for responsive demand."
        else:
            location = "INSIDE_VALUE_AREA"
            location_note = "Price rotating within Value Area. Market in two-sided rotational equilibrium."

        tpo_dist = [
            {"price": p, "tpos": price_bins[p]["count"], "vol": round(price_bins[p]["volume"], 1)}
            for p in sorted_prices
        ]

        return MarketProfileResult(
            symbol=symbol,
            poc=round(poc, 2),
            vah=round(vah, 2),
            val=round(val, 2),
            ib_high=round(ib_high, 2),
            ib_low=round(ib_low, 2),
            ib_range=ib_range,
            range_high=round(range_high, 2),
            range_low=round(range_low, 2),
            total_tpos=total_tpos,
            profile_shape=profile_shape,
            is_balanced=(profile_shape == "D_SHAPE"),
            single_prints=single_prints[:5],
            auction_context={
                "profile_shape": profile_shape,
                "shape_interpretation": shape_desc,
                "location": location,
                "location_note": location_note,
                "ib_extension": "BULLISH_EXPANSION" if current_price > ib_high else ("BEARISH_EXPANSION" if current_price < ib_low else "WITHIN_IB")
            },
            tpo_distribution=tpo_dist
        )


def math_floor(val: float, step: float) -> float:
    return float(np.floor(val / step) * step)


def math_ceil(val: float, step: float) -> float:
    return float(np.ceil(val / step) * step)
