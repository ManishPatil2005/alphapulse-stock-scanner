"""
technicals.py
High-performance technical indicator calculations and market structure analysis:
- RSI (Relative Strength Index with period 21)
- Higher High (HH) & Higher Low (HL) Swing Detection
- Exponential Moving Averages (EMA 20, 50, 200)
- Average True Range (ATR) & Key Support/Resistance Levels
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple


def compute_rsi(close_series: pd.Series, period: int = 21) -> pd.Series:
    """
    Computes Relative Strength Index (RSI) using Wilder's Smoothing.
    Standard technical analysis formula.
    """
    if len(close_series) < period + 1:
        return pd.Series(np.nan, index=close_series.index)

    delta = close_series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # First value is simple average
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    # Apply Wilder's smoothing
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
    """
    Detects pivot swing highs and swing lows.
    A swing high is formed when High[i] >= High in surrounding window.
    A swing low is formed when Low[i] <= Low in surrounding window.
    Returns: (swing_highs, swing_lows)
    """
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

    # Classify swing highs: HH (Higher High) vs LH (Lower High)
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

    # Classify swing lows: HL (Higher Low) vs LL (Lower Low)
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


def analyze_market_structure(
    df: pd.DataFrame,
    rsi_period: int = 21,
    rsi_threshold: float = 50.0,
    swing_window: int = 3
) -> Dict[str, Any]:
    """
    Performs complete market structure analysis for a given stock DataFrame.
    Checks:
      1. Price is making Higher Highs (HH) and Higher Lows (HL)
      2. RSI(21) is above 50 (or custom threshold)
      3. Trend health and support/resistance levels
    """
    if len(df) < 5:
        return {
            'is_valid': False,
            'error': f'Not enough data bars ({len(df)} available, need >= 5)'
        }

    # Calculate indicators
    df['rsi_21'] = compute_rsi(df['close'], period=rsi_period)
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

    # Swings detection
    swing_highs, swing_lows = detect_swings(df, window=swing_window)

    # Evaluate HH (Higher High)
    has_hh = False
    recent_high_price = 0.0
    prev_high_price = 0.0
    recent_high_date = ""

    if len(swing_highs) >= 2:
        recent_h = swing_highs[-1]
        prev_h = swing_highs[-2]
        recent_high_price = recent_h['price']
        prev_high_price = prev_h['price']
        recent_high_date = str(pd.to_datetime(recent_h['time'], unit='s').date())
        # Confirmed HH or current price is breaking out above recent swing high
        if recent_h['price'] > prev_h['price'] or curr_price > recent_h['price']:
            has_hh = True
    elif len(swing_highs) == 1:
        recent_h = swing_highs[0]
        recent_high_price = recent_h['price']
        if curr_price > recent_high_price:
            has_hh = True

    # Evaluate HL (Higher Low)
    has_hl = False
    recent_low_price = 0.0
    prev_low_price = 0.0
    recent_low_date = ""

    if len(swing_lows) >= 2:
        recent_l = swing_lows[-1]
        prev_l = swing_lows[-2]
        recent_low_price = recent_l['price']
        prev_low_price = prev_l['price']
        recent_low_date = str(pd.to_datetime(recent_l['time'], unit='s').date())
        if recent_l['price'] > prev_l['price']:
            has_hl = True
    elif len(swing_lows) == 1:
        recent_l = swing_lows[0]
        recent_low_price = recent_l['price']
        # If low is well above start of dataset
        if recent_low_price > df.iloc[0]['low']:
            has_hl = True

    # Market structure integrity: current price must be sustaining above the recent Higher Low
    structure_intact = curr_price >= recent_low_price if recent_low_price > 0 else True

    # Combined master condition:
    # 1. Price is making HH and HL
    # 2. RSI(21) is above 50
    # 3. Market structure is intact
    passes_scan = bool(has_hh and has_hl and rsi_condition and structure_intact)

    # 20-day Volume Average & Volume Surge
    vol_20_avg = float(df['volume'].iloc[-20:].mean()) if len(df) >= 20 else float(df['volume'].mean())
    curr_vol = float(latest['volume'])
    vol_ratio = (curr_vol / vol_20_avg) if vol_20_avg > 0 else 1.0

    # ATR & Levels
    curr_atr = float(latest['atr_14']) if not np.isnan(latest['atr_14']) else (curr_price * 0.02)
    suggested_stop_loss = round(recent_low_price * 0.992, 2) if recent_low_price > 0 else round(curr_price - 1.5 * curr_atr, 2)
    next_resistance = round(recent_high_price, 2) if recent_high_price > curr_price else round(curr_price + (curr_price - recent_low_price), 2)

    # 52-week High / Low
    high_52w = float(df['high'].max())
    low_52w = float(df['low'].min())

    # Generate chart markers for TradingView Lightweight Charts
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

    # Sort markers by time
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
        'recent_high': round(recent_high_price, 2),
        'prev_high': round(prev_high_price, 2),
        'recent_low': round(recent_low_price, 2),
        'prev_low': round(prev_low_price, 2),
        'suggested_stop_loss': suggested_stop_loss,
        'next_resistance': next_resistance,
        'volume': int(curr_vol),
        'volume_avg_20': int(vol_20_avg),
        'volume_ratio': round(vol_ratio, 2),
        'high_52w': round(high_52w, 2),
        'low_52w': round(low_52w, 2),
        'ema_20': round(float(latest['ema_20']), 2) if not np.isnan(latest['ema_20']) else None,
        'ema_50': round(float(latest['ema_50']), 2) if not np.isnan(latest['ema_50']) else None,
        'ema_200': round(float(latest['ema_200']), 2) if not np.isnan(latest['ema_200']) else None,
        'markers': markers,
        'trend_status': 'Bullish Uptrend (HH + HL)' if (has_hh and has_hl) else ('Higher High Only' if has_hh else ('Higher Low Only' if has_hl else 'Consolidation / Downtrend'))
    }
