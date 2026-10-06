"""
technicals.py
High-performance technical indicator calculations, Smart Money Concepts (SMC/ICT),
Market Profile (POC/VAH/VAL), Episodic Pivots (Earnings/Catalyst Gaps),
Circuit filters (Upper/Lower Circuit locks), and In-Trade Psychology.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple


def compute_rsi(close_series: pd.Series, period: int = 21) -> pd.Series:
    """Computes Relative Strength Index (RSI) using Wilder's Smoothing."""
    if len(close_series) < period + 1:
        return pd.Series(np.nan, index=close_series.index)

    delta = close_series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    gain_vals = gain.values
    loss_vals = loss.values
    ag = avg_gain.values.copy()
    al = avg_loss.values.copy()

    for i in range(period, len(close_series)):
        ag[i] = (ag[i - 1] * (period - 1) + gain_vals[i]) / period
        al[i] = (al[i - 1] * (period - 1) + loss_vals[i]) / period

    rs = np.divide(ag, al, out=np.zeros_like(ag), where=al != 0)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return pd.Series(rsi, index=close_series.index)


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Computes Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Computes Average True Range."""
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def detect_swings(df: pd.DataFrame, window: int = 3) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Detects pivot swing highs and swing lows."""
    n = len(df)
    if n < window * 2 + 2:
        return [], []

    highs = df['high'].values
    lows = df['low'].values
    timestamps = df['time'].values if 'time' in df.columns else df['timestamp'].values

    raw_highs = []
    raw_lows = []

    for i in range(window, n - window):
        left_h = highs[i - window : i]
        right_h = highs[i + 1 : i + window + 1]
        if highs[i] >= np.max(left_h) and highs[i] >= np.max(right_h):
            raw_highs.append({
                'index': i,
                'time': int(timestamps[i]),
                'price': float(highs[i])
            })

        left_l = lows[i - window : i]
        right_l = lows[i + 1 : i + window + 1]
        if lows[i] <= np.min(left_l) and lows[i] <= np.min(right_l):
            raw_lows.append({
                'index': i,
                'time': int(timestamps[i]),
                'price': float(lows[i])
            })

    # Classify swing highs: HH vs LH
    classified_highs = []
    for idx, sh in enumerate(raw_highs):
        item = dict(sh)
        if idx == 0:
            item['type'] = 'H'
            item['label'] = 'H'
        else:
            prev_price = raw_highs[idx - 1]['price']
            if item['price'] > prev_price:
                item['type'] = 'HH'
                item['label'] = 'HH'
            else:
                item['type'] = 'LH'
                item['label'] = 'LH'
            item['prev_price'] = prev_price
            item['change_pct'] = ((item['price'] - prev_price) / prev_price) * 100.0
        classified_highs.append(item)

    # Classify swing lows: HL vs LL
    classified_lows = []
    for idx, sl in enumerate(raw_lows):
        item = dict(sl)
        if idx == 0:
            item['type'] = 'L'
            item['label'] = 'L'
        else:
            prev_price = raw_lows[idx - 1]['price']
            if item['price'] > prev_price:
                item['type'] = 'HL'
                item['label'] = 'HL'
            else:
                item['type'] = 'LL'
                item['label'] = 'LL'
            item['prev_price'] = prev_price
            item['change_pct'] = ((item['price'] - prev_price) / prev_price) * 100.0
        classified_lows.append(item)

    return classified_highs, classified_lows


def check_circuit_lock(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Detects Upper Circuit (UC) and Lower Circuit (LC) locks in cash segment equities.
    Circuit locked stocks have frozen wicks (range ~ 0) and extreme price changes (+/- 5%, 10%, 20%).
    """
    if len(df) < 2:
        return False, "Normal"

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    c = float(latest['close'])
    h = float(latest['high'])
    l = float(latest['low'])
    p_c = float(prev['close'])

    if c <= 0 or p_c <= 0:
        return False, "Normal"

    rng = h - l
    chg_pct = ((c - p_c) / p_c) * 100.0
    is_frozen = (rng / c) <= 0.002 or rng == 0.0

    if is_frozen and chg_pct >= 4.5:
        return True, "Upper Circuit (Locked)"
    if is_frozen and chg_pct <= -4.5:
        return True, "Lower Circuit (Locked)"

    return False, "Normal"


def detect_episodic_pivot(df: pd.DataFrame, min_gap_pct: float = 3.5, min_rvol: float = 2.0) -> Dict[str, Any]:
    """
    Detects Pradeep Bonde (Stockbee) Episodic Pivots:
    - Fundamental catalyst gap up (e.g. Quarterly Earnings surprise) >= 3.5%
    - Massive Volume Surge (RVOL >= 2.0 to 5.0)
    - Strong opening holding drive (closes in top 50% of the day)
    Scans the latest bar or within the last 5 bars for ongoing EP momentum.
    """
    if len(df) < 21:
        return {"is_ep": False, "gap_pct": 0.0, "rvol": 1.0, "bars_ago": -1, "ep_time": None}

    vol_20_series = df['volume'].rolling(20).mean()

    for offset in range(1, min(6, len(df))):
        idx = -offset
        curr = df.iloc[idx]
        prev = df.iloc[idx - 1]
        c = float(curr['close'])
        o = float(curr['open'])
        h = float(curr['high'])
        l = float(curr['low'])
        v = float(curr['volume'])
        p_c = float(prev['close'])
        avg_v = float(vol_20_series.iloc[idx - 1]) if not np.isnan(vol_20_series.iloc[idx - 1]) else 1.0

        if p_c <= 0 or avg_v <= 0:
            continue

        gap_pct = ((o - p_c) / p_c) * 100.0
        rvol = v / avg_v
        total_rng = h - l
        close_strength = ((c - l) / total_rng) if total_rng > 0 else 0.5

        if gap_pct >= min_gap_pct and rvol >= min_rvol and c >= o and close_strength >= 0.40:
            return {
                "is_ep": True,
                "gap_pct": round(gap_pct, 2),
                "rvol": round(rvol, 2),
                "bars_ago": offset - 1,
                "ep_time": int(curr['time']) if 'time' in curr else None,
                "catalyst_note": "Quarterly Earnings / High-Impact Catalyst Gap"
            }

    return {"is_ep": False, "gap_pct": 0.0, "rvol": 1.0, "bars_ago": -1, "ep_time": None}


def detect_fair_value_gaps(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detects ICT/SMC 3-candle Fair Value Gaps (FVG) / Price Imbalances.
    """
    fvgs = []
    if len(df) < 3:
        return fvgs

    n = len(df)
    # Check last 50 bars for active/mitigated FVGs
    start_idx = max(2, n - 50)
    for i in range(start_idx, n):
        bar_0 = df.iloc[i - 2]
        bar_2 = df.iloc[i]

        # Bullish FVG: Low of Bar 2 > High of Bar 0
        if bar_2['low'] > bar_0['high']:
            bottom = float(bar_0['high'])
            top = float(bar_2['low'])
            gap_size = top - bottom
            if gap_size > 0:
                mitigated = False
                for k in range(i + 1, n):
                    if df.iloc[k]['low'] <= bottom:
                        mitigated = True
                        break
                fvgs.append({
                    "type": "Bullish FVG",
                    "time": int(bar_2['time']) if 'time' in bar_2 else i,
                    "top": round(top, 2),
                    "bottom": round(bottom, 2),
                    "size_pct": round((gap_size / bar_2['close']) * 100, 2),
                    "is_mitigated": mitigated
                })

        # Bearish FVG: High of Bar 2 < Low of Bar 0
        elif bar_2['high'] < bar_0['low']:
            top = float(bar_0['low'])
            bottom = float(bar_2['high'])
            gap_size = top - bottom
            if gap_size > 0:
                mitigated = False
                for k in range(i + 1, n):
                    if df.iloc[k]['high'] >= top:
                        mitigated = True
                        break
                fvgs.append({
                    "type": "Bearish FVG",
                    "time": int(bar_2['time']) if 'time' in bar_2 else i,
                    "top": round(top, 2),
                    "bottom": round(bottom, 2),
                    "size_pct": round((gap_size / bar_2['close']) * 100, 2),
                    "is_mitigated": mitigated
                })

    return fvgs


def detect_liquidity_sweeps(
    df: pd.DataFrame,
    swing_highs: List[Dict[str, Any]],
    swing_lows: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Detects ICT/SMC Liquidity Sweeps:
    - Bullish SSL Sweep: Price probes below recent swing low (hunting retail sell stops) but closes back above it.
    - Bearish BSL Sweep: Price probes above recent swing high (hunting retail buy stops) but closes back below it.
    """
    if len(df) < 2:
        return {"has_sweep": False, "sweep_type": "None", "sweep_time": None}

    latest = df.iloc[-1]
    h = float(latest['high'])
    l = float(latest['low'])
    c = float(latest['close'])
    t = int(latest['time']) if 'time' in latest else 0

    # Check SSL (Sell-side liquidity sweep of recent swing low)
    if swing_lows:
        recent_low = swing_lows[-1]['price']
        if l < recent_low and c > recent_low:
            return {
                "has_sweep": True,
                "sweep_type": "Bullish SSL Sweep (Sell Stops Hunted)",
                "sweep_level": round(recent_low, 2),
                "sweep_time": t
            }

    # Check BSL (Buy-side liquidity sweep of recent swing high)
    if swing_highs:
        recent_high = swing_highs[-1]['price']
        if h > recent_high and c < recent_high:
            return {
                "has_sweep": True,
                "sweep_type": "Bearish BSL Sweep (Buy Stops Hunted)",
                "sweep_level": round(recent_high, 2),
                "sweep_time": t
            }

    return {"has_sweep": False, "sweep_type": "None", "sweep_time": None}


def compute_market_profile(df: pd.DataFrame, num_bins: int = 25) -> Dict[str, Any]:
    """
    Computes Market Profile Volume Distribution:
    - Point of Control (POC): Price level of heaviest volume traded.
    - Value Area High (VAH) & Value Area Low (VAL): 70% volume distribution band.
    """
    if len(df) < 5:
        return {"poc": 0.0, "vah": 0.0, "val": 0.0}

    lookback = min(len(df), 120)
    sub_df = df.iloc[-lookback:]

    min_p = float(sub_df['low'].min())
    max_p = float(sub_df['high'].max())

    if max_p <= min_p:
        return {"poc": round(min_p, 2), "vah": round(max_p, 2), "val": round(min_p, 2)}

    bin_size = (max_p - min_p) / num_bins
    price_bins = [min_p + i * bin_size for i in range(num_bins + 1)]
    bin_volumes = np.zeros(num_bins)

    for _, row in sub_df.iterrows():
        row_vol = float(row['volume'])
        row_low = float(row['low'])
        row_high = float(row['high'])
        for b in range(num_bins):
            b_low = price_bins[b]
            b_high = price_bins[b + 1]
            if row_high >= b_low and row_low <= b_high:
                bin_volumes[b] += row_vol

    max_bin_idx = int(np.argmax(bin_volumes))
    poc_price = (price_bins[max_bin_idx] + price_bins[max_bin_idx + 1]) / 2.0

    total_vol = np.sum(bin_volumes)
    target_vol = total_vol * 0.70
    accum_vol = bin_volumes[max_bin_idx]
    low_idx = max_bin_idx
    high_idx = max_bin_idx

    while accum_vol < target_vol and (low_idx > 0 or high_idx < num_bins - 1):
        next_low_vol = bin_volumes[low_idx - 1] if low_idx > 0 else 0
        next_high_vol = bin_volumes[high_idx + 1] if high_idx < num_bins - 1 else 0
        if next_high_vol >= next_low_vol and high_idx < num_bins - 1:
            high_idx += 1
            accum_vol += next_high_vol
        elif low_idx > 0:
            low_idx -= 1
            accum_vol += next_low_vol
        else:
            break

    vah = price_bins[high_idx + 1]
    val = price_bins[low_idx]

    return {
        "poc": round(poc_price, 2),
        "vah": round(vah, 2),
        "val": round(val, 2)
    }


def analyze_market_structure(
    df: pd.DataFrame,
    rsi_period: int = 21,
    rsi_threshold: float = 50.0,
    swing_window: int = 3,
    require_hh_hl: bool = True,
    require_rsi: bool = True,
    require_ema_compression: bool = False,
    require_pinbar_doji: bool = False,
    max_ema_spread_pct: float = 3.5,
    filter_circuits: bool = True,
    require_episodic_pivot: bool = False,
    require_liquidity_sweep: bool = False
) -> Dict[str, Any]:
    """
    Performs complete market structure analysis for a given stock DataFrame.
    Evaluates:
      1. Higher Highs (HH) & Higher Lows (HL)
      2. RSI(21) Above 50
      3. EMA (10, 20, 50) Compression (Coiling Squeeze)
      4. Bullish Pinbar / Doji above EMAs
      5. Upper & Lower Circuit Filter (excludes frozen stocks)
      6. Episodic Pivot (Quarterly Earnings Catalyst Gap & Volume Surge)
      7. Smart Money Concepts (ICT Liquidity Sweeps, FVGs, Order Blocks)
      8. Market Profile (POC, VAH, VAL) & In-Trade Risk Psychology
    """
    if len(df) < 5:
        return {
            'is_valid': False,
            'error': f'Not enough data bars ({len(df)} available, need >= 5)'
        }

    # Calculate indicators
    df['rsi_21'] = compute_rsi(df['close'], period=rsi_period)
    df['ema_10'] = compute_ema(df['close'], 10)
    df['ema_20'] = compute_ema(df['close'], 20)
    df['ema_50'] = compute_ema(df['close'], 50)
    df['ema_200'] = compute_ema(df['close'], 200) if len(df) >= 200 else pd.Series(np.nan, index=df.index)
    df['atr_14'] = compute_atr(df['high'], df['low'], df['close'], 14)

    latest = df.iloc[-1]
    prev_close = df.iloc[-2]['close'] if len(df) >= 2 else latest['close']

    curr_price = float(latest['close'])
    price_change = curr_price - prev_close
    price_change_pct = (price_change / prev_close) * 100.0 if prev_close != 0 else 0.0

    curr_rsi = float(latest['rsi_21']) if not np.isnan(latest['rsi_21']) else 0.0
    rsi_condition = curr_rsi >= rsi_threshold

    # Swings detection (HH & HL)
    swing_highs, swing_lows = detect_swings(df, window=swing_window)

    # Evaluate HH
    has_hh = False
    recent_high_price = 0.0
    prev_high_price = 0.0

    if len(swing_highs) >= 2:
        recent_h = swing_highs[-1]
        prev_h = swing_highs[-2]
        recent_high_price = recent_h['price']
        prev_high_price = prev_h['price']
        if recent_h['price'] > prev_h['price'] or curr_price > recent_h['price']:
            has_hh = True
    elif len(swing_highs) == 1:
        recent_h = swing_highs[0]
        recent_high_price = recent_h['price']
        if curr_price > recent_high_price:
            has_hh = True

    # Evaluate HL
    has_hl = False
    recent_low_price = 0.0
    prev_low_price = 0.0

    if len(swing_lows) >= 2:
        recent_l = swing_lows[-1]
        prev_l = swing_lows[-2]
        recent_low_price = recent_l['price']
        prev_low_price = prev_l['price']
        if recent_l['price'] > prev_l['price']:
            has_hl = True
    elif len(swing_lows) == 1:
        recent_l = swing_lows[0]
        recent_low_price = recent_l['price']
        if recent_low_price > df.iloc[0]['low']:
            has_hl = True

    structure_intact = curr_price >= recent_low_price if recent_low_price > 0 else True

    # --- RULE 3: EMA Compression (10, 20, 50) ---
    spreads = []
    for offset in [-1, -2, -3]:
        if abs(offset) <= len(df):
            row_bar = df.iloc[offset]
            c_val = float(row_bar['close'])
            e10 = float(row_bar['ema_10'])
            e20 = float(row_bar['ema_20'])
            e50 = float(row_bar['ema_50'])
            if c_val > 0 and not (np.isnan(e10) or np.isnan(e20) or np.isnan(e50)):
                sp = ((max(e10, e20, e50) - min(e10, e20, e50)) / c_val) * 100.0
                spreads.append(sp)

    curr_ema_spread_pct = round(spreads[0], 2) if spreads else 999.0
    min_recent_spread = min(spreads) if spreads else 999.0
    has_ema_compression = (min_recent_spread <= max_ema_spread_pct)

    # --- RULE 4: Bullish Pinbar / Doji above EMAs ---
    candle_pattern = "Standard Candle"
    is_above_emas = False
    has_pinbar_or_doji = False
    pinbar_candle_time = None

    def check_candle(row_bar):
        o = float(row_bar['open'])
        h = float(row_bar['high'])
        l = float(row_bar['low'])
        c = float(row_bar['close'])
        rng = h - l
        if rng <= 0:
            return "Standard Candle", False, False
        body = abs(c - o)
        lower_shadow = min(o, c) - l
        upper_shadow = h - max(o, c)

        e10 = float(row_bar['ema_10'])
        e20 = float(row_bar['ema_20'])
        e50 = float(row_bar['ema_50'])
        min_ema = min(e10, e20, e50)
        max_ema = max(e10, e20, e50)

        above = (c >= min_ema * 0.995) and (h >= max_ema * 0.99)
        is_pin = (
            lower_shadow >= 1.25 * body and
            lower_shadow >= 0.38 * rng and
            upper_shadow <= 0.35 * rng and
            c >= l + 0.45 * rng
        )
        is_dj = (
            body <= 0.22 * rng and
            (lower_shadow >= 0.25 * rng or c >= l + 0.40 * rng)
        )
        pat = "Bullish Pinbar" if is_pin else ("Doji" if is_dj else "Standard Candle")
        matched = (is_pin or is_dj) and above
        return pat, above, matched

    pat_1, above_1, match_1 = check_candle(latest)
    if match_1:
        candle_pattern = pat_1
        is_above_emas = above_1
        has_pinbar_or_doji = True
        pinbar_candle_time = int(latest['time']) if 'time' in latest else None
    elif len(df) >= 2:
        prev_bar = df.iloc[-2]
        pat_2, above_2, match_2 = check_candle(prev_bar)
        if match_2:
            candle_pattern = f"{pat_2} (Prev Bar)"
            is_above_emas = above_2
            has_pinbar_or_doji = True
            pinbar_candle_time = int(prev_bar['time']) if 'time' in prev_bar else None
        else:
            candle_pattern = pat_1
            is_above_emas = above_1
    else:
        candle_pattern = pat_1
        is_above_emas = above_1

    # --- RULE 5: Upper / Lower Circuit Filter ---
    is_circuit_locked, circuit_status = check_circuit_lock(df)

    # --- RULE 6: Episodic Pivot (Quarterly Earnings Catalyst Gap & Volume) ---
    ep_data = detect_episodic_pivot(df)

    # --- RULE 7: SMC / ICT Liquidity Sweeps & FVGs ---
    liquidity_sweep = detect_liquidity_sweeps(df, swing_highs, swing_lows)
    fair_value_gaps = detect_fair_value_gaps(df)

    # --- RULE 8: Market Profile POC & Value Area ---
    market_profile = compute_market_profile(df)

    # --- Master Filter Check ---
    hh_hl_ok = bool(has_hh and has_hl and structure_intact)
    rsi_ok = bool(rsi_condition)
    comp_ok = bool(has_ema_compression)
    candle_ok = bool(has_pinbar_or_doji)
    ep_ok = bool(ep_data.get("is_ep", False))
    sweep_ok = bool(liquidity_sweep.get("has_sweep", False))

    passes = True
    if filter_circuits and is_circuit_locked:
        passes = False
    if require_hh_hl and not hh_hl_ok:
        passes = False
    if require_rsi and not rsi_ok:
        passes = False
    if require_ema_compression and not comp_ok:
        passes = False
    if require_pinbar_doji and not candle_ok:
        passes = False
    if require_episodic_pivot and not ep_ok:
        passes = False
    if require_liquidity_sweep and not sweep_ok:
        passes = False

    passes_scan = bool(passes)

    # Volume Statistics
    vol_20_avg = float(df['volume'].iloc[-20:].mean()) if len(df) >= 20 else float(df['volume'].mean())
    curr_vol = float(latest['volume'])
    vol_ratio = (curr_vol / vol_20_avg) if vol_20_avg > 0 else 1.0

    # ATR & Levels
    curr_atr = float(latest['atr_14']) if not np.isnan(latest['atr_14']) else (curr_price * 0.02)
    suggested_stop_loss = round(recent_low_price * 0.992, 2) if recent_low_price > 0 else round(curr_price - 1.5 * curr_atr, 2)
    risk_distance = max(0.01, curr_price - suggested_stop_loss)
    target_1 = round(curr_price + 2.0 * risk_distance, 2)
    target_2 = round(curr_price + 3.0 * risk_distance, 2)
    next_resistance = round(recent_high_price, 2) if recent_high_price > curr_price else target_1

    # In-Trade Psychology & FOMO Guardrails
    ema_10_val = float(latest['ema_10']) if not np.isnan(latest['ema_10']) else curr_price
    dist_from_ema10 = ((curr_price - ema_10_val) / ema_10_val) * 100.0 if ema_10_val > 0 else 0.0
    fomo_risk = "High Risk (Extended >4.5% above EMA 10, wait for pullback)" if (dist_from_ema10 > 4.5 or curr_rsi > 72) else "Optimal Entry (Near EMA Support Zone)"

    # 52-week High / Low
    high_52w = float(df['high'].max())
    low_52w = float(df['low'].min())

    # Generate Chart Markers for TradingView Lightweight Charts
    markers = []
    for sh in swing_highs:
        markers.append({
            'time': sh['time'],
            'position': 'aboveBar',
            'color': '#10b981' if sh.get('type') == 'HH' else '#f59e0b',
            'shape': 'arrowDown',
            'text': sh.get('label', 'H'),
            'size': 1.5
        })
    for sl in swing_lows:
        markers.append({
            'time': sl['time'],
            'position': 'belowBar',
            'color': '#06b6d4' if sl.get('type') == 'HL' else '#ef4444',
            'shape': 'arrowUp',
            'text': sl.get('label', 'L'),
            'size': 1.5
        })

    # Add marker for Pinbar / Doji
    if has_pinbar_or_doji and pinbar_candle_time:
        pat_badge = "📌 PIN" if "Pinbar" in candle_pattern else "⚖️ DOJI"
        markers.append({
            'time': pinbar_candle_time,
            'position': 'belowBar',
            'color': '#a855f7',
            'shape': 'circle',
            'text': pat_badge,
            'size': 1.8
        })

    # Add marker for Episodic Pivot
    if ep_data.get("is_ep") and ep_data.get("ep_time"):
        markers.append({
            'time': ep_data["ep_time"],
            'position': 'belowBar',
            'color': '#ec4899',
            'shape': 'arrowUp',
            'text': f"🚀 EP +{ep_data['gap_pct']}%",
            'size': 2.0
        })

    # Add marker for Liquidity Sweep
    if liquidity_sweep.get("has_sweep") and liquidity_sweep.get("sweep_time"):
        is_bull_sweep = "Bullish" in liquidity_sweep["sweep_type"]
        markers.append({
            'time': liquidity_sweep["sweep_time"],
            'position': 'belowBar' if is_bull_sweep else 'aboveBar',
            'color': '#06b6d4' if is_bull_sweep else '#ef4444',
            'shape': 'arrowUp' if is_bull_sweep else 'arrowDown',
            'text': "⚡ SSL SWEEP" if is_bull_sweep else "⚡ BSL SWEEP",
            'size': 2.0
        })

    markers.sort(key=lambda m: m['time'])

    return {
        'is_valid': True,
        'passes_scan': passes_scan,
        'price': round(curr_price, 2),
        'change': round(price_change, 2),
        'change_pct': round(price_change_pct, 2),
        'rsi_21': round(curr_rsi, 2),
        'rsi_condition': rsi_condition,
        'has_hh': has_hh,
        'has_hl': has_hl,
        'structure_intact': structure_intact,
        'has_ema_compression': has_ema_compression,
        'ema_spread_pct': curr_ema_spread_pct,
        'candle_pattern': candle_pattern,
        'is_above_emas': is_above_emas,
        'has_pinbar_or_doji': has_pinbar_or_doji,
        'is_circuit_locked': is_circuit_locked,
        'circuit_status': circuit_status,
        'episodic_pivot': ep_data,
        'liquidity_sweep': liquidity_sweep,
        'market_profile': market_profile,
        'fair_value_gaps': fair_value_gaps[-5:],  # Return top 5 recent FVGs
        'recent_high': round(recent_high_price, 2),
        'prev_high': round(prev_high_price, 2),
        'recent_low': round(recent_low_price, 2),
        'prev_low': round(prev_low_price, 2),
        'suggested_stop_loss': suggested_stop_loss,
        'target_1': target_1,
        'target_2': target_2,
        'risk_reward_ratio': "1:2 / 1:3",
        'next_resistance': next_resistance,
        'volume': int(curr_vol),
        'volume_avg_20': int(vol_20_avg),
        'volume_ratio': round(vol_ratio, 2),
        'high_52w': round(high_52w, 2),
        'low_52w': round(low_52w, 2),
        'ema_10': round(float(latest['ema_10']), 2) if not np.isnan(latest['ema_10']) else None,
        'ema_20': round(float(latest['ema_20']), 2) if not np.isnan(latest['ema_20']) else None,
        'ema_50': round(float(latest['ema_50']), 2) if not np.isnan(latest['ema_50']) else None,
        'ema_200': round(float(latest['ema_200']), 2) if not np.isnan(latest['ema_200']) else None,
        'markers': markers,
        'trade_psychology': {
            'risk_reward_ratio': 2.0,
            'fomo_risk': fomo_risk,
            'fomo_risk_level': "HIGH RISK (CHASING)" if (dist_from_ema10 > 4.5 or curr_rsi > 72) else ("MODERATE" if dist_from_ema10 > 2.5 else "SAFE (VALUE ENTRY)"),
            'dist_from_ema10': round(dist_from_ema10, 2),
            'invalidation_sl': suggested_stop_loss,
            'position_risk_amount': 1000.0,
            'recommended_shares': int(1000.0 / risk_distance) if risk_distance > 0 else 0,
            'target_1': target_1,
            'target_2': target_2,
            'max_risk_pct': "1.0% - 1.5% of total capital",
            'position_shares_formula': "Risk Amount / (Entry Price - Stop Loss)"
        },
        'trend_status': 'Bullish Uptrend (HH + HL)' if (has_hh and has_hl) else ('Higher High Only' if has_hh else ('Higher Low Only' if has_hl else 'Consolidation / Downtrend'))
    }
