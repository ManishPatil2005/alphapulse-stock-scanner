"""
backtest_engine/monte_carlo.py
Monte Carlo Simulations for Strategy Robustness.
"""

import numpy as np
import pandas as pd
from typing import List, Dict

class MonteCarloEngine:
    def __init__(self, trades: List[float], initial_capital: float = 100000.0):
        """trades is a list of realized PnL values per trade."""
        self.trades = trades
        self.initial_capital = initial_capital

    def run_simulation(self, iterations: int = 1000, risk_of_ruin_level: float = 0.5) -> Dict:
        """
        Resamples trades randomly with replacement to generate equity curves.
        Evaluates Probability of Ruin and Median Drawdown.
        """
        if not self.trades:
            return {}

        n_trades = len(self.trades)
        final_equities = []
        max_drawdowns = []
        ruin_count = 0
        ruin_threshold = self.initial_capital * risk_of_ruin_level

        for _ in range(iterations):
            # Resample indices
            resampled_trades = np.random.choice(self.trades, size=n_trades, replace=True)
            
            equity_curve = [self.initial_capital]
            current_equity = self.initial_capital
            peak_equity = self.initial_capital
            max_dd = 0.0
            ruined = False
            
            for pnl in resampled_trades:
                current_equity += pnl
                equity_curve.append(current_equity)
                
                if current_equity > peak_equity:
                    peak_equity = current_equity
                
                dd = (peak_equity - current_equity) / peak_equity
                if dd > max_dd:
                    max_dd = dd
                    
                if current_equity <= ruin_threshold and not ruined:
                    ruined = True
                    ruin_count += 1
            
            final_equities.append(current_equity)
            max_drawdowns.append(max_dd)

        final_equities = np.array(final_equities)
        max_drawdowns = np.array(max_drawdowns)

        return {
            "Median Final Equity": round(np.median(final_equities), 2),
            "5th Percentile Equity": round(np.percentile(final_equities, 5), 2),
            "95th Percentile Equity": round(np.percentile(final_equities, 95), 2),
            "Median Max Drawdown (%)": round(np.median(max_drawdowns) * 100, 2),
            "95th Percentile Max Drawdown (%)": round(np.percentile(max_drawdowns, 95) * 100, 2),
            "Probability of Ruin (%)": round((ruin_count / iterations) * 100, 2)
        }
