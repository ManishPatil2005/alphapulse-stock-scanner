"""
learning_engine/psychology.py
The In-Trade Psychology Cockpit.
Analyzes live or paper trades to detect emotional and irrational trading patterns.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta

class PsychologyCockpit:
    """
    Detects behavioral anti-patterns in trading data:
    - Revenge Trading (Multiple trades entered immediately after a loss)
    - Averaging Down (Adding to a losing position at a worse price)
    - Moving Stops (Widening stop losses to avoid taking a loss)
    - Overleveraging (Risking > 5% of account on a single trade)
    """

    def __init__(self, risk_tolerance_pct: float = 0.05):
        self.risk_tolerance_pct = risk_tolerance_pct

    def analyze_session(self, trades: List[Dict[str, Any]], order_modifications: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Expects a list of trades with:
        {'id', 'timestamp', 'symbol', 'direction', 'entry_price', 'exit_price', 'pnl', 'capital_risked', 'account_value'}
        
        Expects order modifications with:
        {'trade_id', 'timestamp', 'old_stop', 'new_stop', 'entry_price', 'direction'}
        """
        flags = []
        score = 100.0  # Start with perfect psychology score
        
        # 1. Detect Revenge Trading
        # (Entering a trade within 10 minutes of a losing trade)
        trades = sorted(trades, key=lambda x: x['timestamp'])
        for i in range(1, len(trades)):
            prev_trade = trades[i-1]
            curr_trade = trades[i]
            
            if prev_trade['pnl'] < 0:
                time_diff = curr_trade['timestamp'] - prev_trade['timestamp']
                if time_diff <= timedelta(minutes=10):
                    flags.append({
                        "type": "Revenge Trading",
                        "severity": "HIGH",
                        "message": f"Trade {curr_trade['id']} on {curr_trade['symbol']} was entered just {time_diff.total_seconds()//60} mins after a loss."
                    })
                    score -= 15.0

        # 2. Detect Overleveraging
        for t in trades:
            if 'capital_risked' in t and 'account_value' in t:
                risk_pct = t['capital_risked'] / t['account_value']
                if risk_pct > self.risk_tolerance_pct:
                    flags.append({
                        "type": "Overleveraging",
                        "severity": "CRITICAL",
                        "message": f"Trade {t['id']} risked {risk_pct*100:.1f}% of account, exceeding safe threshold of {self.risk_tolerance_pct*100:.1f}%."
                    })
                    score -= 20.0

        # 3. Detect Averaging Down (Requires granular entry data, simplified here based on same symbol sequences)
        # If consecutive trades are the same symbol, same direction, and second entry is worse, AND it's a loss.
        for i in range(1, len(trades)):
            prev = trades[i-1]
            curr = trades[i]
            
            if prev['symbol'] == curr['symbol'] and prev['direction'] == curr['direction']:
                # Assume they are part of the same scaling operation for paper trading
                is_averaging_down = False
                if curr['direction'] == 'LONG' and curr['entry_price'] < prev['entry_price'] and prev['pnl'] < 0:
                    is_averaging_down = True
                elif curr['direction'] == 'SHORT' and curr['entry_price'] > prev['entry_price'] and prev['pnl'] < 0:
                    is_averaging_down = True
                    
                if is_averaging_down:
                    flags.append({
                        "type": "Averaging Down",
                        "severity": "HIGH",
                        "message": f"Added to losing position on {curr['symbol']} at {curr['entry_price']}."
                    })
                    score -= 10.0

        # 4. Detect Moving Stops
        if order_modifications:
            for mod in order_modifications:
                if mod['direction'] == 'LONG' and mod['new_stop'] < mod['old_stop']:
                    flags.append({
                        "type": "Moving Stop Loss",
                        "severity": "CRITICAL",
                        "message": f"Stop loss widened from {mod['old_stop']} to {mod['new_stop']} on LONG position."
                    })
                    score -= 25.0
                elif mod['direction'] == 'SHORT' and mod['new_stop'] > mod['old_stop']:
                    flags.append({
                        "type": "Moving Stop Loss",
                        "severity": "CRITICAL",
                        "message": f"Stop loss widened from {mod['old_stop']} to {mod['new_stop']} on SHORT position."
                    })
                    score -= 25.0

        score = max(0.0, score)
        
        return {
            "psychology_score": round(score, 1),
            "total_trades_analyzed": len(trades),
            "flags": flags,
            "summary": self._generate_summary(score, flags)
        }

    def _generate_summary(self, score: float, flags: List[Dict]) -> str:
        if score >= 90:
            return "Excellent discipline. You adhered to risk management rules."
        elif score >= 70:
            return "Good session, but slight emotional leakage detected. Review flags."
        elif score >= 50:
            return "Warning: Significant psychological biases detected. Step away from the screens."
        else:
            return "TILT DETECTED: You have lost emotional control. Trading halted."
