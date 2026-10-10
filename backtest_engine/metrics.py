"""
backtest_engine/metrics.py
Calculates institutional-grade performance metrics from an equity curve and trade list.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any

def calculate_metrics(equity_curve: pd.DataFrame, trades: List[Dict]) -> Dict[str, Any]:
    if equity_curve.empty or len(trades) == 0:
        return {"status": "error", "message": "No trades executed."}
        
    equity_curve['returns'] = equity_curve['equity'].pct_change().fillna(0)
    
    # 1. Total Return
    initial_cap = equity_curve['equity'].iloc[0]
    final_cap = equity_curve['equity'].iloc[-1]
    total_return_pct = (final_cap - initial_cap) / initial_cap
    
    # 2. CAGR (assuming daily bars for 252 trading days)
    days = (equity_curve.index[-1] - equity_curve.index[0]).days
    if days > 0:
        cagr = ((final_cap / initial_cap) ** (365.25 / days)) - 1
    else:
        cagr = 0.0

    # 3. Sharpe & Sortino Ratios (Annualized)
    risk_free_rate = 0.02
    daily_rf = risk_free_rate / 252
    excess_returns = equity_curve['returns'] - daily_rf
    
    std_dev = equity_curve['returns'].std()
    sharpe = np.sqrt(252) * (excess_returns.mean() / std_dev) if std_dev > 0 else 0
    
    downside_returns = excess_returns[excess_returns < 0]
    downside_std = downside_returns.std()
    sortino = np.sqrt(252) * (excess_returns.mean() / downside_std) if downside_std > 0 else 0

    # 4. Max Drawdown
    equity_curve['cum_max'] = equity_curve['equity'].cummax()
    drawdown = (equity_curve['equity'] - equity_curve['cum_max']) / equity_curve['cum_max']
    max_dd = drawdown.min()

    # 5. Trade Analytics
    winning_trades = 0
    losing_trades = 0
    gross_profit = 0.0
    gross_loss = 0.0
    
    trade_pnl = []
    
    # Simple pairing of LONG and EXIT (Assumption: sequential full entries/exits)
    # We will compute realized PnL by matching BUYs and SELLs.
    buy_price = 0
    
    for t in trades:
        if t['direction'] == 'BUY':
            buy_price = t['price']
        elif t['direction'] == 'SELL' and buy_price > 0:
            pnl = (t['price'] - buy_price) * t['quantity']
            # Deduct fees approximation for round trip
            pnl -= (t['commission'] * 2) + (t['slippage'] * 2)
            trade_pnl.append(pnl)
            if pnl > 0:
                winning_trades += 1
                gross_profit += pnl
            else:
                losing_trades += 1
                gross_loss += abs(pnl)
            buy_price = 0

    total_closed_trades = winning_trades + losing_trades
    win_rate = winning_trades / total_closed_trades if total_closed_trades > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (99.9 if gross_profit > 0 else 0)

    return {
        "Total Return (%)": round(total_return_pct * 100, 2),
        "CAGR (%)": round(cagr * 100, 2),
        "Sharpe Ratio": round(sharpe, 2),
        "Sortino Ratio": round(sortino, 2),
        "Max Drawdown (%)": round(max_dd * 100, 2),
        "Total Trades": total_closed_trades,
        "Win Rate (%)": round(win_rate * 100, 2),
        "Profit Factor": round(profit_factor, 2)
    }
