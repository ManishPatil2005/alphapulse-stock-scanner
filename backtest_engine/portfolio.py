"""
backtest_engine/portfolio.py
Manages positions, cash, equity curve, and generates OrderEvents from SignalEvents.
"""

from typing import Dict, List, Optional
import pandas as pd
from queue import Queue

from .events import SignalEvent, OrderEvent, FillEvent, EventType

class Portfolio:
    def __init__(self, events_queue: Queue, initial_capital: float = 100000.0, risk_per_trade_pct: float = 0.02):
        self.events_queue = events_queue
        self.initial_capital = initial_capital
        self.risk_per_trade_pct = risk_per_trade_pct
        
        self.current_cash = initial_capital
        self.positions: Dict[str, int] = {}
        self.holdings: Dict[str, float] = {}  # Cost basis
        
        self.equity_curve: List[Dict[str, float]] = []
        self.trade_history: List[Dict] = []
        
        self.last_timestamp = None

    def update_market_value(self, symbol: str, current_price: float, timestamp: pd.Timestamp):
        """Called on MARKET events to update current equity curve."""
        self.last_timestamp = timestamp
        
        market_value = 0.0
        for sym, qty in self.positions.items():
            if sym == symbol:
                market_value += qty * current_price
            else:
                # Approximate other holdings if multi-asset, currently assume single asset updates
                pass 
                
        total_equity = self.current_cash + market_value
        
        self.equity_curve.append({
            "timestamp": timestamp,
            "equity": total_equity,
            "cash": self.current_cash,
            "drawdown": 0.0 # Computed later
        })

    def update_signal(self, event: SignalEvent, current_price: float):
        """Converts SignalEvent to OrderEvent with position sizing."""
        symbol = event.symbol
        direction = event.signal_type
        
        # Current position
        cur_qty = self.positions.get(symbol, 0)
        
        if direction == 'LONG' and cur_qty == 0:
            # Sizing logic: Risk fixed percentage of current equity
            equity = self.current_cash
            if len(self.equity_curve) > 0:
                equity = self.equity_curve[-1]['equity']
                
            capital_to_deploy = equity * self.risk_per_trade_pct * 10 # Assuming 10x leverage or arbitrary size for demo
            
            # Simple un-leveraged size:
            qty = int((equity * 0.95) / current_price) # Deploy 95% of equity for all-in strategy test
            if qty > 0:
                order = OrderEvent(symbol, "MKT", qty, "BUY")
                self.events_queue.put(order)
                
        elif direction == 'EXIT' and cur_qty > 0:
            order = OrderEvent(symbol, "MKT", cur_qty, "SELL")
            self.events_queue.put(order)

    def update_fill(self, event: FillEvent):
        """Updates portfolio on fill."""
        fill_dir = 1 if event.direction == 'BUY' else -1
        fill_cost = event.fill_price * event.quantity * fill_dir
        
        # Update cash
        self.current_cash -= (fill_cost + event.commission + event.slippage)
        
        # Update positions
        self.positions[event.symbol] = self.positions.get(event.symbol, 0) + (event.quantity * fill_dir)
        
        # Record trade
        self.trade_history.append({
            "timestamp": event.timestamp,
            "symbol": event.symbol,
            "direction": event.direction,
            "quantity": event.quantity,
            "price": event.fill_price,
            "commission": event.commission,
            "slippage": event.slippage,
            "cash_after": self.current_cash
        })

    def get_equity_curve_df(self) -> pd.DataFrame:
        if not self.equity_curve:
            return pd.DataFrame()
            
        df = pd.DataFrame(self.equity_curve)
        df.set_index('timestamp', inplace=True)
        # Compute drawdown
        df['high_water_mark'] = df['equity'].cummax()
        df['drawdown'] = (df['equity'] - df['high_water_mark']) / df['high_water_mark']
        return df
