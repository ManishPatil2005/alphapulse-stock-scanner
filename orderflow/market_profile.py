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
    poor_high: bool = False
    poor_low: bool = False
    excess_high: bool = False
    excess_low: bool = False
    rotation_factor: int = 0
    vpoc: float = 0.0
    day_high: float = 0.0
    day_low: float = 0.0
    prev_day_high: float = 0.0
    prev_day_low: float = 0.0
    prev_day_close: float = 0.0
    open_price: float = 0.0
    vwap: float = 0.0
    opening_range: float = 0.0
    total_volume: float = 0.0
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    buy_trades: int = 0
    sell_trades: int = 0
    developing_poc: List[Dict[str, Any]] = field(default_factory=list)
    volume_profile: List[Dict[str, Any]] = field(default_factory=list)
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

        # Determine dynamic tick bucket size based on total range (target ~35 TPO bins)
        total_range = float(df["high"].max() - df["low"].min()) if len(df) > 0 else 10.0
        raw_bucket = max(0.0001, total_range / 35.0)
        if raw_bucket > 50:
            bucket_size = round(raw_bucket / 10.0) * 10.0
        elif raw_bucket > 5:
            bucket_size = round(raw_bucket)
        elif raw_bucket > 1:
            bucket_size = round(raw_bucket * 2.0) / 2.0
        elif raw_bucket > 0.1:
            bucket_size = round(raw_bucket * 10.0) / 10.0
        elif raw_bucket > 0.01:
            bucket_size = round(raw_bucket * 100.0) / 100.0
        else:
            bucket_size = max(0.0001, round(raw_bucket * 10000.0) / 10000.0)

        price_bins: Dict[float, Dict[str, Any]] = {}
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

        # Calculate Initial Balance (IB: first ib_periods bars)
        ib_df = df.iloc[:min(ib_periods, len(df))]
        ib_high = float(ib_df["high"].max())
        ib_low = float(ib_df["low"].min())
        ib_range = round(ib_high - ib_low, 2)

        # Reference levels
        day_high = float(df["high"].max())
        day_low = float(df["low"].min())
        open_price = float(df["open"].iloc[0])
        close_price = float(df["close"].iloc[-1])
        opening_range = round(float(df["high"].iloc[0] - df["low"].iloc[0]), 2)

        # Previous day estimates
        prev_slice = df.iloc[:-min(len(df) // 2, 25)] if len(df) >= 20 else df
        prev_day_high = float(prev_slice["high"].max())
        prev_day_low = float(prev_slice["low"].min())
        prev_day_close = float(prev_slice["close"].iloc[-1])

        # VWAP calculation
        typical_prices = (df["high"] + df["low"] + df["close"]) / 3.0
        vwap_val = float((typical_prices * df["volume"]).sum() / max(1.0, df["volume"].sum()))

        # Dalton Rotation Factor calculation
        rotation_factor = 0
        for i in range(1, len(df)):
            prev_h = df["high"].iloc[i - 1]
            curr_h = df["high"].iloc[i]
            prev_l = df["low"].iloc[i - 1]
            curr_l = df["low"].iloc[i]
            if curr_h > prev_h:
                rotation_factor += 1
            elif curr_h < prev_h:
                rotation_factor -= 1
            if curr_l > prev_l:
                rotation_factor += 1
            elif curr_l < prev_l:
                rotation_factor -= 1

        total_tpos = 0
        tot_vol = float(df["volume"].sum())
        buy_vol = 0.0
        sell_vol = 0.0
        developing_pocs: List[Dict[str, Any]] = []

        # Construct TPO matrix & tracking developing POC
        for idx, row in df.iterrows():
            period_letter = letters[idx % len(letters)]
            low_b = math_floor(row["low"], bucket_size)
            high_b = math_ceil(row["high"], bucket_size)

            curr = low_b
            steps = max(1, int(round((high_b - low_b) / bucket_size)) + 1)
            vol_per_step = float(row["volume"]) / steps

            is_up = row["close"] >= row["open"]
            bar_buy = float(row["volume"]) * (0.65 if is_up else 0.35)
            bar_sell = float(row["volume"]) - bar_buy
            buy_vol += bar_buy
            sell_vol += bar_sell

            while curr <= high_b:
                rounded_p = round(curr, 2)
                if rounded_p not in price_bins:
                    price_bins[rounded_p] = {
                        "count": 0,
                        "volume": 0.0,
                        "buy_volume": 0.0,
                        "sell_volume": 0.0,
                        "periods": []
                    }
                price_bins[rounded_p]["count"] += 1
                price_bins[rounded_p]["volume"] += vol_per_step
                step_buy = vol_per_step * (0.65 if is_up else 0.35)
                price_bins[rounded_p]["buy_volume"] += step_buy
                price_bins[rounded_p]["sell_volume"] += (vol_per_step - step_buy)

                if period_letter not in price_bins[rounded_p]["periods"]:
                    price_bins[rounded_p]["periods"].append(period_letter)
                total_tpos += 1
                curr = round(curr + bucket_size, 4)

            # Record developing POC at this bar
            cur_poc = max(price_bins.keys(), key=lambda p: (price_bins[p]["count"], price_bins[p]["volume"]))
            developing_pocs.append({
                "period": period_letter,
                "time": str(row.get("time", idx)),
                "poc": round(cur_poc, 2)
            })

        if not price_bins:
            return None

        # Point of Control (POC): Price level with maximum TPO count
        sorted_prices = sorted(price_bins.keys())
        poc = max(sorted_prices, key=lambda p: (price_bins[p]["count"], price_bins[p]["volume"]))

        # Volume POC (vPOC): Price level with maximum traded volume
        vpoc = max(sorted_prices, key=lambda p: price_bins[p]["volume"])

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

        # Poor High & Poor Low detection
        poor_high = bool(price_bins[range_high]["count"] >= 2)
        poor_low = bool(price_bins[range_low]["count"] >= 2)

        # Excess High & Excess Low (clean single-print rejection tails >= 2 price bins)
        excess_high = bool(len(sorted_prices) >= 3 and price_bins[range_high]["count"] == 1 and price_bins[sorted_prices[-2]]["count"] == 1)
        excess_low = bool(len(sorted_prices) >= 3 and price_bins[range_low]["count"] == 1 and price_bins[sorted_prices[1]]["count"] == 1)

        # Single Prints (levels with exactly 1 TPO in middle of range)
        single_prints = [
            float(p) for p in sorted_prices[1:-1]
            if price_bins[p]["count"] == 1 and val < p < vah
        ]

        # Profile Shape Classification
        poc_relative_pos = (poc - range_low) / max(0.01, (range_high - range_low))
        if poc_relative_pos > 0.65:
            profile_shape = "P_SHAPE"
            shape_desc = "P-Shape Profile: Short covering or initiative buyers establishing acceptance at highs."
        elif poc_relative_pos < 0.35:
            profile_shape = "b_SHAPE"
            shape_desc = "b-Shape Profile: Long liquidation or initiative sellers establishing acceptance at lows."
        elif 0.40 <= poc_relative_pos <= 0.60:
            profile_shape = "D_SHAPE"
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

        # High Volume Nodes (HVN) and Low Volume Nodes (LVN)
        vol_threshold_hvn = float(np.percentile([price_bins[p]["volume"] for p in sorted_prices], 80))
        vol_threshold_lvn = float(np.percentile([price_bins[p]["volume"] for p in sorted_prices], 25))

        volume_profile = [
            {
                "price": float(p),
                "volume": round(float(price_bins[p]["volume"]), 1),
                "buy_volume": round(float(price_bins[p]["buy_volume"]), 1),
                "sell_volume": round(float(price_bins[p]["sell_volume"]), 1),
                "is_hvn": bool(price_bins[p]["volume"] >= vol_threshold_hvn),
                "is_lvn": bool(price_bins[p]["volume"] <= vol_threshold_lvn),
                "is_vpoc": bool(abs(p - vpoc) < 0.001),
                "is_in_va": bool(val <= p <= vah)
            }
            for p in sorted_prices
        ]

        tpo_dist = [
            {
                "price": float(p),
                "tpos": int(price_bins[p]["count"]),
                "letters": "".join(price_bins[p]["periods"]),
                "periods": list(price_bins[p]["periods"]),
                "vol": round(float(price_bins[p]["volume"]), 1),
                "is_poc": bool(abs(p - poc) < 0.001),
                "is_vah": bool(abs(p - vah) < 0.001),
                "is_val": bool(abs(p - val) < 0.001),
                "is_in_va": bool(val <= p <= vah)
            }
            for p in sorted_prices
        ]

        # Trade counts estimate
        avg_trade_size = max(10, tot_vol / max(1, len(df) * 4))
        buy_trades = int(buy_vol / avg_trade_size)
        sell_trades = int(sell_vol / avg_trade_size)

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
            poor_high=poor_high,
            poor_low=poor_low,
            excess_high=excess_high,
            excess_low=excess_low,
            rotation_factor=rotation_factor,
            vpoc=round(vpoc, 2),
            day_high=round(day_high, 2),
            day_low=round(day_low, 2),
            prev_day_high=round(prev_day_high, 2),
            prev_day_low=round(prev_day_low, 2),
            prev_day_close=round(prev_day_close, 2),
            open_price=round(open_price, 2),
            vwap=round(vwap_val, 2),
            opening_range=opening_range,
            total_volume=round(tot_vol, 1),
            buy_volume=round(buy_vol, 1),
            sell_volume=round(sell_vol, 1),
            buy_trades=buy_trades,
            sell_trades=sell_trades,
            developing_poc=developing_pocs[-30:],
            volume_profile=volume_profile,
            auction_context={
                "profile_shape": profile_shape,
                "shape_interpretation": shape_desc,
                "location": location,
                "location_note": location_note,
                "rotation_factor": rotation_factor,
                "ib_extension": "BULLISH_EXPANSION" if current_price > ib_high else ("BEARISH_EXPANSION" if current_price < ib_low else "WITHIN_IB")
            },
            tpo_distribution=tpo_dist
        )


def math_floor(val: float, step: float) -> float:
    return float(np.floor(val / step) * step)


def math_ceil(val: float, step: float) -> float:
    return float(np.ceil(val / step) * step)
