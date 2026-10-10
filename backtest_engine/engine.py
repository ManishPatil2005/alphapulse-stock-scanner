"""
backtest_engine/engine.py
Core Event-Driven Backtest Loop.
"""

from queue import Queue, Empty
import pandas as pd
from typing import Dict, Any

from .events import EventType, MarketEvent, SignalEvent
from .portfolio import Portfolio
from .execution import ExecutionHandler

class EventDrivenBacktester:
    def __init__(self, symbol: str, data: pd.DataFrame, strategy_ast: Dict[str, Any] = None):
        self.symbol = symbol
        self.data = data
        self.strategy_ast = strategy_ast
        self.events = Queue()
        
        self.portfolio = Portfolio(self.events, initial_capital=100000.0)
        self.execution = ExecutionHandler(self.events)
        
        self.current_idx = 0
        self.total_bars = len(data)
        
    def _run_strategy(self, idx: int, current_row: pd.Series):
        """
        Evaluates strategy logic. For this integration, we will trigger a simple
        moving average crossover if no AST is provided, or evaluate AST.
        """
        if idx < 20:
            return
            
        current_price = current_row['close']
        timestamp = current_row['time'] if 'time' in current_row else current_row.name
        
        # MOCK STRATEGY: EMA 10 Crosses EMA 20
        prev_row = self.data.iloc[idx-1]
        
        # Entry
        if prev_row['ema_10'] <= prev_row['ema_20'] and current_row['ema_10'] > current_row['ema_20']:
            signal = SignalEvent(self.symbol, timestamp, 'LONG')
            self.events.put(signal)
            
        # Exit
        elif prev_row['ema_10'] >= prev_row['ema_20'] and current_row['ema_10'] < current_row['ema_20']:
            signal = SignalEvent(self.symbol, timestamp, 'EXIT')
            self.events.put(signal)

    def run(self):
        """Main event loop."""
        print(f"Starting Event-Driven Backtest for {self.symbol}...")
        
        # Convert time column to datetime if not index
        if 'time' in self.data.columns and not pd.api.types.is_datetime64_any_dtype(self.data['time']):
             self.data['time'] = pd.to_datetime(self.data['time'], unit='s')
        
        while self.current_idx < self.total_bars:
            # 1. Push Market Event
            current_row = self.data.iloc[self.current_idx]
            timestamp = current_row['time'] if 'time' in current_row else current_row.name
            current_price = current_row['close']
            
            self.events.put(MarketEvent())
            
            # 2. Process Queue
            while True:
                try:
                    event = self.events.get(False)
                except Empty:
                    break
                else:
                    if event.type == EventType.MARKET:
                        self._run_strategy(self.current_idx, current_row)
                        self.portfolio.update_market_value(self.symbol, current_price, timestamp)
                        
                    elif event.type == EventType.SIGNAL:
                        self.portfolio.update_signal(event, current_price)
                        
                    elif event.type == EventType.ORDER:
                        self.execution.execute_order(event, current_price, timestamp)
                        
                    elif event.type == EventType.FILL:
                        self.portfolio.update_fill(event)
            
            self.current_idx += 1
            
        print("Backtest Complete.")
        return self.portfolio.get_equity_curve_df(), self.portfolio.trade_history
