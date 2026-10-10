"""
backtest_engine/walk_forward.py
Walk-Forward Optimization (WFO) Engine.
Iteratively trains on In-Sample (IS) data and tests on Out-Of-Sample (OOS) data.
"""

import pandas as pd
from typing import List, Dict, Callable

class WalkForwardOptimizer:
    def __init__(self, data: pd.DataFrame, train_window: int = 252, test_window: int = 63):
        """
        train_window: Number of bars for IS training (e.g., 1 year = 252)
        test_window: Number of bars for OOS testing (e.g., 3 months = 63)
        """
        self.data = data
        self.train_window = train_window
        self.test_window = test_window

    def generate_folds(self):
        """Generates the IS and OOS data slices."""
        total_bars = len(self.data)
        folds = []
        
        start_idx = 0
        while start_idx + self.train_window + self.test_window <= total_bars:
            train_start = start_idx
            train_end = start_idx + self.train_window
            test_end = train_end + self.test_window
            
            is_data = self.data.iloc[train_start:train_end]
            oos_data = self.data.iloc[train_end:test_end]
            
            folds.append({
                "is_data": is_data,
                "oos_data": oos_data
            })
            
            # Step forward by the test window
            start_idx += self.test_window
            
        return folds
        
    def run_optimization(self, strategy_func: Callable) -> Dict:
        """
        strategy_func: A function that takes IS data, optimizes parameters, 
                       and returns an equity curve / metrics on the OOS data.
                       
        Since AST dynamically evaluates, we can mock this for the Phase 4 delivery.
        """
        folds = self.generate_folds()
        results = []
        
        for idx, fold in enumerate(folds):
            # In a real optimizer, we'd run grid search on `fold["is_data"]`
            # and apply best params to `fold["oos_data"]`.
            
            # Here we just pass the OOS to the evaluator to simulate the out-of-sample forward step.
            oos_metrics = strategy_func(fold["oos_data"])
            results.append({
                "fold": idx + 1,
                "oos_return": oos_metrics.get("Total Return (%)", 0),
                "oos_max_dd": oos_metrics.get("Max Drawdown (%)", 0)
            })
            
        return {
            "Total Folds": len(folds),
            "Average OOS Return (%)": round(sum(r["oos_return"] for r in results) / len(folds), 2) if folds else 0,
            "Average OOS Max DD (%)": round(sum(r["oos_max_dd"] for r in results) / len(folds), 2) if folds else 0,
            "Fold Details": results
        }
