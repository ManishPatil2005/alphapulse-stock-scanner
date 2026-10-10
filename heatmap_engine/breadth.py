"""
heatmap_engine/breadth.py
Calculates global market breadth indicators (Advance/Decline, % Above 50 EMA, etc.).
"""

import pandas as pd
from typing import List, Dict, Any
from technicals import compute_ema
from data_feed import get_stock_data

class MarketBreadthEngine:
    def __init__(self, symbols: List[str]):
        self.symbols = symbols

    def calculate_breadth(self) -> Dict[str, Any]:
        advancing = 0
        declining = 0
        unchanged = 0
        
        above_20_ema = 0
        above_50_ema = 0
        above_200_ema = 0
        
        total_processed = 0

        for sym in self.symbols:
            df, _ = get_stock_data(sym, interval="1d", data_range="1y")
            if df is None or len(df) < 200:
                continue
                
            total_processed += 1
            last_close = df['close'].iloc[-1]
            prev_close = df['close'].iloc[-2]
            
            # A/D Logic
            if last_close > prev_close:
                advancing += 1
            elif last_close < prev_close:
                declining += 1
            else:
                unchanged += 1
                
            # EMA Breadth Logic
            ema_20 = compute_ema(df['close'], 20).iloc[-1]
            ema_50 = compute_ema(df['close'], 50).iloc[-1]
            ema_200 = compute_ema(df['close'], 200).iloc[-1]
            
            if last_close > ema_20: above_20_ema += 1
            if last_close > ema_50: above_50_ema += 1
            if last_close > ema_200: above_200_ema += 1

        if total_processed == 0:
            return {"error": "Insufficient data"}
            
        return {
            "total_symbols": total_processed,
            "advance_decline": {
                "advancing": advancing,
                "declining": declining,
                "unchanged": unchanged,
                "ratio": round(advancing / declining, 2) if declining > 0 else advancing
            },
            "ema_breadth": {
                "pct_above_20": round((above_20_ema / total_processed) * 100, 2),
                "pct_above_50": round((above_50_ema / total_processed) * 100, 2),
                "pct_above_200": round((above_200_ema / total_processed) * 100, 2)
            },
            "market_state": self._determine_market_state(advancing, declining, above_50_ema, total_processed)
        }

    def _determine_market_state(self, adv: int, dec: int, above_50: int, total: int) -> str:
        pct_above_50 = above_50 / total
        if pct_above_50 > 0.75 and adv > dec:
            return "Extreme Greed / Overbought"
        elif pct_above_50 > 0.5 and adv > dec:
            return "Healthy Bull Market"
        elif pct_above_50 < 0.25 and adv < dec:
            return "Extreme Fear / Oversold"
        elif pct_above_50 < 0.5 and adv < dec:
            return "Bear Market Control"
        else:
            return "Mixed / Choppy"
