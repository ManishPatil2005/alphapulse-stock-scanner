"""
backtest_engine/execution.py
Simulated execution handler to model Broker latency, Slippage, and Commissions.
"""

from queue import Queue
from .events import OrderEvent, FillEvent

class ExecutionHandler:
    def __init__(self, events_queue: Queue, commission_pct: float = 0.001, slippage_pct: float = 0.0005):
        self.events_queue = events_queue
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct

    def execute_order(self, event: OrderEvent, current_market_price: float, current_timestamp):
        """
        Takes an OrderEvent and creates a FillEvent.
        Applies mathematical models for slippage and trading fees.
        """
        # Calculate realistic fill price
        if event.direction == 'BUY':
            fill_price = current_market_price * (1.0 + self.slippage_pct)
        else:
            fill_price = current_market_price * (1.0 - self.slippage_pct)

        # Calculate commission
        commission = fill_price * event.quantity * self.commission_pct

        fill_event = FillEvent(
            timestamp=current_timestamp,
            symbol=event.symbol,
            exchange="SIMULATED",
            quantity=event.quantity,
            direction=event.direction,
            fill_price=fill_price,
            commission=commission,
            slippage=abs(fill_price - current_market_price) * event.quantity
        )
        
        self.events_queue.put(fill_event)
