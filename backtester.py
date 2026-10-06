"""
backtester.py
Institutional Backtesting Engine for AlphaPulse Stock Scanner Strategies.
Simulates bar-by-bar execution with exact entry, stop-loss, profit-target rules,
position sizing, equity curves, drawdown calculations, and trade analytics.
"""

import math
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from data_feed import get_stock_data
from technicals import (
    compute_rsi,
    compute_ema,
    compute_atr,
    detect_swings,
    check_circuit_lock,
    detect_episodic_pivot,
    detect_fair_value_gaps,
    detect_liquidity_sweeps
)


def run_strategy_backtest(
    symbol: str,
    timeframe: str = "1d",
    data_range: str = "1y",
    strategy: str = "master",
    risk_reward: float = 2.0,
    initial_capital: float = 100000.0,
    risk_per_trade_pct: float = 1.0,
    max_holding_bars: int = 40
) -> Dict[str, Any]:
    """
    Executes a historical bar-by-bar backtest of the selected scanner strategy.

    Strategies supported:
      - 'master': AlphaPulse Master Setup (RSI21 > 50 + HH/HL + EMA Compression + Bullish Pinbar/Doji)
      - 'episodic_pivot': Stockbee Quarterly Earnings Catalyst Gap-Up with 2x+ Volume Surge
      - 'smc_sweep': ICT / Smart Money Liquidity Sweep & Squeeze
      - 'ema_squeeze': Pure EMA 10/20/50 Coiling Squeeze Breakout
      - 'rsi_trend': RSI(21) Momentum + Market Structure Trend Following
    """
    symbol = symbol.strip().upper()

    try:
        df, meta = get_stock_data(symbol, interval=timeframe, data_range=data_range)
    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "message": f"Data fetch failed: {str(e)}"
        }

    if df is None or len(df) < 55:
        return {
            "symbol": symbol,
            "status": "error",
            "message": f"Insufficient historical bars ({len(df) if df is not None else 0}) for reliable backtest (minimum 55 required)."
        }

    # Ensure required columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for c in required_cols:
        if c not in df.columns:
            return {"symbol": symbol, "status": "error", "message": f"Missing column: {c}"}

    # Precalculate indicators across whole history
    df = df.copy()
    df['rsi_21'] = compute_rsi(df['close'], period=21)
    df['ema_10'] = compute_ema(df['close'], 10)
    df['ema_20'] = compute_ema(df['close'], 20)
    df['ema_50'] = compute_ema(df['close'], 50)
    df['atr_14'] = compute_atr(df['high'], df['low'], df['close'], 14)
    df['vol_ma20'] = df['volume'].rolling(window=20, min_periods=5).mean()

    timestamps = df['time'].values if 'time' in df.columns else df['timestamp'].values
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    volumes = df['volume'].values
    rvol_series = (df['volume'] / df['vol_ma20'].replace(0, np.nan)).fillna(1.0).values

    rsi_vals = df['rsi_21'].values
    ema10_vals = df['ema_10'].values
    ema20_vals = df['ema_20'].values
    ema50_vals = df['ema_50'].values
    atr_vals = df['atr_14'].values

    # Backtest simulation state
    capital = initial_capital
    peak_capital = capital
    equity_curve = [{"time": int(timestamps[50]), "equity": round(capital, 2)}]
    trades: List[Dict[str, Any]] = []

    in_position = False
    current_trade: Optional[Dict[str, Any]] = None

    # Warmup period of 50 bars for indicator stability
    warmup = 50
    total_bars = len(df)

    for i in range(warmup, total_bars):
        curr_time = int(timestamps[i])
        curr_open = float(opens[i])
        curr_high = float(highs[i])
        curr_low = float(lows[i])
        curr_close = float(closes[i])
        curr_vol = float(volumes[i])
        curr_atr = float(atr_vals[i]) if not np.isnan(atr_vals[i]) else (curr_close * 0.02)
        if curr_atr <= 0:
            curr_atr = curr_close * 0.02

        # -------------------------------------------------------------
        # 1. Manage Active Position
        # -------------------------------------------------------------
        if in_position and current_trade is not None:
            entry_price = current_trade["entry_price"]
            stop_loss = current_trade["stop_loss"]
            target_price = current_trade["target_price"]
            shares = current_trade["shares"]
            bars_held = i - current_trade["entry_bar_idx"]

            exit_happened = False
            exit_price = 0.0
            exit_reason = ""
            outcome = ""

            # Check Stop Loss first (worst case gap down or touch)
            if curr_low <= stop_loss:
                # If opened below stop loss, fill at open (slippage realism)
                exit_price = min(curr_open, stop_loss)
                exit_reason = "STOP_LOSS"
                outcome = "LOSS"
                exit_happened = True
            # Check Target
            elif curr_high >= target_price:
                # If opened above target, fill at open
                exit_price = max(curr_open, target_price)
                exit_reason = "PROFIT_TARGET"
                outcome = "WIN"
                exit_happened = True
            # Check Max Holding Timeout
            elif bars_held >= max_holding_bars:
                exit_price = curr_close
                exit_reason = "TIME_EXPIRY"
                outcome = "WIN" if exit_price > entry_price else "LOSS"
                exit_happened = True
            # End of historical data
            elif i == total_bars - 1:
                exit_price = curr_close
                exit_reason = "END_OF_DATA"
                outcome = "WIN" if exit_price > entry_price else "LOSS"
                exit_happened = True

            if exit_happened:
                pnl_dollars = (exit_price - entry_price) * shares
                pnl_pct = ((exit_price - entry_price) / entry_price) * 100.0
                capital += pnl_dollars

                if capital > peak_capital:
                    peak_capital = capital

                trade_record = {
                    "trade_num": len(trades) + 1,
                    "symbol": symbol,
                    "entry_time": current_trade["entry_time"],
                    "exit_time": curr_time,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(exit_price, 2),
                    "stop_loss": round(stop_loss, 2),
                    "target_price": round(target_price, 2),
                    "shares": shares,
                    "pnl_dollars": round(pnl_dollars, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "outcome": outcome,
                    "exit_reason": exit_reason,
                    "bars_held": bars_held,
                    "capital_after": round(capital, 2)
                }
                trades.append(trade_record)
                equity_curve.append({"time": curr_time, "equity": round(capital, 2)})

                in_position = False
                current_trade = None
                continue  # Evaluated exit; cannot enter new trade on same bar

        # -------------------------------------------------------------
        # 2. Evaluate Strategy Entry Signals (When not in position)
        # -------------------------------------------------------------
        if not in_position and i < total_bars - 1:
            # Check Circuit lock on current bar (skip illiquid / circuit frozen)
            if curr_close > 0 and (curr_high - curr_low) / curr_close < 0.002:
                continue

            rsi_val = rsi_vals[i]
            e10 = ema10_vals[i]
            e20 = ema20_vals[i]
            e50 = ema50_vals[i]

            if np.isnan(rsi_val) or np.isnan(e10) or np.isnan(e20) or np.isnan(e50):
                continue

            # EMA spread coiling
            spread_pct = ((max(e10, e20, e50) - min(e10, e20, e50)) / curr_close) * 100.0
            is_ema_compressed = (spread_pct <= 3.8)

            # Candle classification
            candle_body = abs(curr_close - curr_open)
            candle_range = curr_high - curr_low
            lower_wick = min(curr_open, curr_close) - curr_low

            is_pinbar = (candle_range > 0 and (lower_wick / candle_range) >= 0.50 and curr_close > curr_low + 0.4 * candle_range)
            is_doji = (candle_range > 0 and (candle_body / candle_range) <= 0.20)
            is_bullish_candle = is_pinbar or is_doji or (curr_close >= curr_open and curr_close > e10)

            # HH/HL check over past 10 bars
            past_10_highs = highs[max(0, i - 10) : i]
            past_10_lows = lows[max(0, i - 10) : i]
            is_hh_hl = (curr_close > np.mean(past_10_highs)) and (curr_low > np.min(past_10_lows))

            # Episodic Pivot check
            prev_close_bar = closes[i - 1]
            gap_pct = ((curr_open - prev_close_bar) / prev_close_bar) * 100.0 if prev_close_bar > 0 else 0.0
            rvol = rvol_series[i]
            is_ep = (gap_pct >= 3.5 and rvol >= 2.0 and curr_close >= curr_open)

            # Smart Money Liquidity Sweep check
            recent_min_5 = np.min(lows[max(0, i - 5) : i])
            is_smc_sweep = (curr_low < recent_min_5 and curr_close > recent_min_5 and curr_close >= curr_open)

            signal_fired = False

            if strategy == "master":
                # AlphaPulse Master Setup
                if rsi_val >= 50.0 and is_hh_hl and is_ema_compressed and is_bullish_candle:
                    signal_fired = True
            elif strategy == "episodic_pivot":
                # Bonde / Stockbee Episodic Pivot
                if is_ep:
                    signal_fired = True
            elif strategy == "smc_sweep":
                # ICT / SMC Liquidity Sweep & Squeeze
                if is_smc_sweep and rsi_val >= 48.0:
                    signal_fired = True
            elif strategy == "ema_squeeze":
                # EMA Compression Breakout
                if is_ema_compressed and curr_close > max(e10, e20, e50) and rsi_val >= 50.0:
                    signal_fired = True
            elif strategy == "rsi_trend":
                # RSI 21 Momentum
                if rsi_val >= 50.0 and is_hh_hl and curr_close > e20:
                    signal_fired = True

            if signal_fired:
                entry_price = curr_close

                # Stop loss based on structural swing or ATR
                sl_distance = max(curr_atr * 1.5, entry_price * 0.018)
                stop_loss = max(0.01, entry_price - sl_distance)
                target_price = entry_price + (sl_distance * risk_reward)

                # Position sizing based on account risk
                risk_capital = capital * (risk_per_trade_pct / 100.0)
                shares = math.floor(risk_capital / sl_distance) if sl_distance > 0 else 0
                max_affordable_shares = math.floor(capital / entry_price) if entry_price > 0 else 0
                shares = min(shares, max_affordable_shares)

                if shares > 0:
                    in_position = True
                    current_trade = {
                        "entry_bar_idx": i,
                        "entry_time": curr_time,
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "target_price": target_price,
                        "shares": shares,
                        "risk_dollars": round(risk_capital, 2)
                    }

    # -------------------------------------------------------------
    # 3. Calculate Performance Metrics
    # -------------------------------------------------------------
    total_trades = len(trades)
    winning_trades = [t for t in trades if t["outcome"] == "WIN"]
    losing_trades = [t for t in trades if t["outcome"] == "LOSS"]

    win_count = len(winning_trades)
    loss_count = len(losing_trades)
    win_rate_pct = round((win_count / total_trades) * 100.0, 1) if total_trades > 0 else 0.0

    gross_profit = sum(t["pnl_dollars"] for t in winning_trades)
    gross_loss = abs(sum(t["pnl_dollars"] for t in losing_trades))
    net_profit = round(gross_profit - gross_loss, 2)
    total_return_pct = round(((capital - initial_capital) / initial_capital) * 100.0, 2)

    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 1.0)

    # Max Drawdown calculation
    drawdowns = []
    running_peak = initial_capital
    for pt in equity_curve:
        eq = pt["equity"]
        if eq > running_peak:
            running_peak = eq
        dd = ((running_peak - eq) / running_peak) * 100.0 if running_peak > 0 else 0.0
        drawdowns.append(dd)

    max_drawdown_pct = round(max(drawdowns), 2) if drawdowns else 0.0

    avg_win_pct = round(np.mean([t["pnl_pct"] for t in winning_trades]), 2) if winning_trades else 0.0
    avg_loss_pct = round(np.mean([t["pnl_pct"] for t in losing_trades]), 2) if losing_trades else 0.0

    # Max consecutive wins & losses
    max_streak_wins = 0
    max_streak_loss = 0
    curr_streak_w = 0
    curr_streak_l = 0

    for t in trades:
        if t["outcome"] == "WIN":
            curr_streak_w += 1
            curr_streak_l = 0
            if curr_streak_w > max_streak_wins:
                max_streak_wins = curr_streak_w
        else:
            curr_streak_l += 1
            curr_streak_w = 0
            if curr_streak_l > max_streak_loss:
                max_streak_loss = curr_streak_l

    return {
        "symbol": symbol,
        "strategy": strategy,
        "timeframe": timeframe,
        "data_range": data_range,
        "status": "success",
        "initial_capital": initial_capital,
        "ending_capital": round(capital, 2),
        "net_profit": net_profit,
        "total_return_pct": total_return_pct,
        "total_trades": total_trades,
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate_pct": win_rate_pct,
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_drawdown_pct,
        "risk_reward_ratio": risk_reward,
        "avg_win_pct": avg_win_pct,
        "avg_loss_pct": avg_loss_pct,
        "max_consecutive_wins": max_streak_wins,
        "max_consecutive_losses": max_streak_loss,
        "equity_curve": equity_curve,
        "trades": trades[-50:]  # Return most recent 50 trades for clean UI payload
    }
